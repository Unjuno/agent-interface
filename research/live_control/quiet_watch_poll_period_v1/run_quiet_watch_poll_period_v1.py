#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, random, statistics, threading, time
from pathlib import Path
import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest

ROI_X=48; ROI_Y=48; ROI_W=32; ROI_H=32
TARGET_RGB=(220,50,50)
TARGET_BGR=bytes((50,50,220))
CLEAR='#101010'
TARGET='#dc3232'
NUISANCE='#dc3232'
DEADLINE_MS=600
FINAL_DELAY_MS=60
CUE_MS=5
TARGET_THRESHOLD=512


def now_ns(): return time.perf_counter_ns()
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def query_right_down(dpy, keycode):
    raw=dpy.query_keymap()
    if isinstance(raw,str): raw=raw.encode('latin1')
    elif not isinstance(raw,(bytes,bytearray)): raw=bytes(raw)
    return bool(raw[keycode // 8] & (1 << (keycode % 8)))

def roi_match_count(raw):
    # Xvfb 24-depth root images are 32-bpp BGRX here; fail if shape is unexpected.
    if len(raw) != ROI_W*ROI_H*4:
        raise RuntimeError(f'unexpected ROI byte count {len(raw)}')
    cnt=0
    for i in range(0,len(raw),4):
        if raw[i:i+3] == TARGET_BGR:
            cnt += 1
    return cnt

def acquire_roi(dpy, root):
    s=now_ns()
    img=root.get_image(ROI_X, ROI_Y, ROI_W, ROI_H, X.ZPixmap, 0xffffffff)
    e=now_ns()
    raw=img.data.encode('latin1') if isinstance(img.data,str) else bytes(img.data)
    return s,e,raw,roi_match_count(raw)

def make_schedule(seed=21620260916, reps=3, nuisance_per_arm=4, offsets=(150,152,154,156,158)):
    cases=[]
    idx=0
    for rep in range(reps):
        for offset in offsets:
            for period in (10,2):
                cases.append({'case_id':f'target-p{period}-o{offset}-r{rep}', 'kind':'target', 'period_ms':period, 'offset_ms':offset})
    for j in range(nuisance_per_arm):
        offset=offsets[j % len(offsets)]
        for period in (10,2):
            cases.append({'case_id':f'nuisance-p{period}-o{offset}-r{j}', 'kind':'nuisance', 'period_ms':period, 'offset_ms':offset})
    rng=random.Random(seed); rng.shuffle(cases)
    for i,c in enumerate(cases): c['order']=i
    return cases

def run_case(case, display_name):
    root=tk.Tk(); root.geometry('640x400+0+0'); root.configure(bg=CLEAR); root.title(case['case_id'])
    canvas=tk.Canvas(root,width=640,height=400,bg=CLEAR,highlightthickness=0); canvas.pack(fill='both',expand=True)
    target_rect=canvas.create_rectangle(ROI_X,ROI_Y,ROI_X+ROI_W-1,ROI_Y+ROI_H-1,fill=CLEAR,outline=CLEAR)
    nuisance_rect=canvas.create_rectangle(160,48,191,79,fill=CLEAR,outline=CLEAR)
    events=[]; events_lock=threading.Lock(); app_pressed=threading.Event(); cancel_event=threading.Event(); stop_event=threading.Event()
    acquisitions=[]; pixels={}; watcher_meta={}; owner_meta={}; cue_meta={}
    root.update(); root.focus_force(); root.update()
    d_owner=display.Display(display_name); d_watch=display.Display(display_name); d_verify=display.Display(display_name)
    xroot=d_watch.screen().root
    keysym=XK.string_to_keysym('Right'); keycode=d_owner.keysym_to_keycode(keysym)
    if not keycode: raise RuntimeError('Right keycode missing')

    def log_event(kind):
        with events_lock: events.append({'kind':kind,'t_ns':now_ns()})
    def on_press(evt):
        log_event('app_key_press'); app_pressed.set()
    def on_release(evt): log_event('app_key_release')
    root.bind('<KeyPress-Right>', on_press); root.bind('<KeyRelease-Right>', on_release)

    def owner():
        xtest.fake_input(d_owner,X.KeyPress,keycode); d_owner.sync(); owner_meta['xtest_press_ns']=now_ns()
        if not app_pressed.wait(1.0):
            owner_meta['error']='app_press_timeout'; stop_event.set(); return
        owner_meta['app_press_seen_ns']=now_ns(); deadline_ns=owner_meta['app_press_seen_ns']+DEADLINE_MS*1_000_000; owner_meta['deadline_ns']=deadline_ns
        while True:
            rem=(deadline_ns-now_ns())/1e9
            if rem <= 0:
                owner_meta['release_reason']='deadline'; break
            if cancel_event.wait(min(rem,0.002)):
                owner_meta['release_reason']='watcher_cancel'; break
        owner_meta['release_command_ns']=now_ns(); xtest.fake_input(d_owner,X.KeyRelease,keycode); d_owner.sync(); owner_meta['release_sync_ns']=now_ns()
        # bounded keymap verification
        verify_deadline=now_ns()+100_000_000
        while now_ns()<verify_deadline:
            if not query_right_down(d_verify,keycode):
                owner_meta['verified_empty_ns']=now_ns(); owner_meta['verified_empty']=True; break
            time.sleep(0.0005)
        else:
            owner_meta['verified_empty']=False
        stop_event.set()

    def watcher():
        if not app_pressed.wait(1.0): watcher_meta['error']='app_press_timeout'; return
        period_ns=case['period_ms']*1_000_000
        next_due=now_ns()
        watcher_meta['start_ns']=next_due
        while not stop_event.is_set():
            rem=next_due-now_ns()
            if rem>0: time.sleep(rem/1e9)
            s,e,raw,count=acquire_roi(d_watch,xroot)
            dig=sha256_bytes(raw); pixels.setdefault(dig,base64.b64encode(raw).decode('ascii'))
            acquisitions.append({'start_ns':s,'end_ns':e,'digest':dig,'match_count':count})
            if count>=TARGET_THRESHOLD and not cancel_event.is_set():
                watcher_meta['detected_ns']=e; watcher_meta['detected_match_count']=count; cancel_event.set()
            next_due += period_ns
            # If far behind, skip missed nominal slots rather than burst-catch-up.
            n=now_ns()
            if next_due < n-period_ns:
                missed=(n-next_due)//period_ns
                next_due += (missed+1)*period_ns
        watcher_meta['end_ns']=now_ns()

    th_owner=threading.Thread(target=owner,daemon=True); th_watch=threading.Thread(target=watcher,daemon=True)
    th_owner.start(); th_watch.start()

    # Wait for app-observed press while pumping Tk.
    tlimit=time.time()+1.0
    while not app_pressed.is_set() and time.time()<tlimit:
        root.update(); time.sleep(0.0002)
    if not app_pressed.is_set():
        stop_event.set(); raise RuntimeError('app did not receive press')
    app_press_ns=min(e['t_ns'] for e in events if e['kind']=='app_key_press')
    cue_on_due=app_press_ns+case['offset_ms']*1_000_000
    cue_off_due=None
    cue_on_done=False; cue_off_done=False
    final_due=app_press_ns+(DEADLINE_MS+FINAL_DELAY_MS)*1_000_000
    while now_ns() < final_due:
        n=now_ns()
        if not cue_on_done and n>=cue_on_due:
            item=target_rect if case['kind']=='target' else nuisance_rect
            canvas.itemconfigure(item,fill=TARGET,outline=TARGET); root.update_idletasks(); root.update()
            cue_meta['on_draw_complete_ns']=now_ns(); cue_off_due=cue_meta['on_draw_complete_ns']+CUE_MS*1_000_000; cue_on_done=True
        if cue_on_done and not cue_off_done and cue_off_due is not None and n>=cue_off_due:
            item=target_rect if case['kind']=='target' else nuisance_rect
            canvas.itemconfigure(item,fill=CLEAR,outline=CLEAR); root.update_idletasks(); root.update()
            cue_meta['off_draw_complete_ns']=now_ns(); cue_off_done=True
        root.update(); time.sleep(0.0002)
    stop_event.set(); th_owner.join(0.3); th_watch.join(0.3); root.update()
    fs,fe,fraw,fcount=acquire_roi(d_watch,xroot); fdig=sha256_bytes(fraw); pixels.setdefault(fdig,base64.b64encode(fraw).decode('ascii'))
    final={'start_ns':fs,'end_ns':fe,'digest':fdig,'match_count':fcount}
    right_down=query_right_down(d_verify,keycode)
    root.destroy(); d_owner.close(); d_watch.close(); d_verify.close()
    # derived
    evs=sorted(events,key=lambda x:x['t_ns']); app_release=[e['t_ns'] for e in evs if e['kind']=='app_key_release']
    detected='detected_ns' in watcher_meta
    gaps=[]
    acq=sorted(acquisitions,key=lambda x:x['start_ns'])
    for a,b in zip(acq,acq[1:]): gaps.append((b['start_ns']-a['end_ns'])/1e6)
    cue_duration_ms=(cue_meta['off_draw_complete_ns']-cue_meta['on_draw_complete_ns'])/1e6
    return {
      'case':case,'events':evs,'owner':owner_meta,'watcher':watcher_meta,'cue':cue_meta,
      'acquisitions':acq,'pixel_payloads':pixels,'final':final,'right_down_final':right_down,
      'derived':{
        'detected':detected,'cue_duration_ms':cue_duration_ms,
        'cue_to_app_release_ms': ((app_release[0]-cue_meta['on_draw_complete_ns'])/1e6 if app_release else None),
        'deadline_to_verified_empty_ms': ((owner_meta.get('verified_empty_ns',0)-owner_meta.get('deadline_ns',0))/1e6 if owner_meta.get('verified_empty_ns') else None),
        'acquisition_count':len(acq),
        'acquisition_wall_ms':sum((a['end_ns']-a['start_ns']) for a in acq)/1e6,
        'max_end_to_next_start_gap_ms':max(gaps) if gaps else None,
      }
    }

def summarize(records):
    out={'arms':{},'integrity':{}}
    for p in (10,2):
        rs=[r for r in records if r['case']['period_ms']==p]
        tar=[r for r in rs if r['case']['kind']=='target']; nui=[r for r in rs if r['case']['kind']=='nuisance']
        det=sum(r['derived']['detected'] for r in tar); false=sum(r['derived']['detected'] for r in nui)
        rel=[r['derived']['cue_to_app_release_ms'] for r in tar if r['derived']['cue_to_app_release_ms'] is not None]
        costs=[r['derived']['acquisition_wall_ms'] for r in nui]
        counts=[r['derived']['acquisition_count'] for r in nui]
        gaps=[r['derived']['max_end_to_next_start_gap_ms'] for r in nui if r['derived']['max_end_to_next_start_gap_ms'] is not None]
        out['arms'][str(p)]={
          'target_detected':det,'target_total':len(tar),'nuisance_false_cancel':false,'nuisance_total':len(nui),
          'target_release_ms_median':statistics.median(rel) if rel else None,
          'nuisance_acquisition_wall_ms_median':statistics.median(costs) if costs else None,
          'nuisance_acquisition_count_median':statistics.median(counts) if counts else None,
          'nuisance_max_gap_ms_max':max(gaps) if gaps else None,
        }
    out['integrity']={
      'verified_empty_all':all(r['owner'].get('verified_empty') and not r['right_down_final'] for r in records),
      'final_roi_clear_all':all(r['final']['match_count']<TARGET_THRESHOLD for r in records),
      'one_press_one_release_all':all(sum(e['kind']=='app_key_press' for e in r['events'])==1 and sum(e['kind']=='app_key_release' for e in r['events'])==1 for r in records),
    }
    a10=out['arms']['10']; a2=out['arms']['2']
    # Declared decision: candidate only if safety/integrity all pass, no nuisance false cancels,
    # strictly more detections, and nuisance acquisition wall time <= 5x baseline median.
    gates=out['integrity']['verified_empty_all'] and out['integrity']['final_roi_clear_all'] and out['integrity']['one_press_one_release_all'] and a10['nuisance_false_cancel']==0 and a2['nuisance_false_cancel']==0
    if not gates: decision='FAIL_SAFETY_OR_INTEGRITY'
    elif a2['target_detected']>a10['target_detected'] and a2['nuisance_acquisition_wall_ms_median'] <= 5*a10['nuisance_acquisition_wall_ms_median']:
        decision='PROMOTE_2MS_SCOPED'
    elif a2['target_detected']>a10['target_detected']:
        decision='HOLD_DETECTION_GAIN_COST_GATE_FAIL'
    else: decision='HOLD_NO_DETECTION_GAIN'
    out['decision']=decision
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--display',default=':99'); ap.add_argument('--preflight',action='store_true'); args=ap.parse_args()
    if args.preflight:
        schedule=[
          {'case_id':'preflight-target-p10','kind':'target','period_ms':10,'offset_ms':150,'order':0},
          {'case_id':'preflight-target-p2','kind':'target','period_ms':2,'offset_ms':150,'order':1},
          {'case_id':'preflight-nuisance-p10','kind':'nuisance','period_ms':10,'offset_ms':150,'order':2},
          {'case_id':'preflight-nuisance-p2','kind':'nuisance','period_ms':2,'offset_ms':150,'order':3}
        ]
    else: schedule=make_schedule()
    records=[]
    for c in schedule:
        records.append(run_case(c,args.display))
    payload={'schema':'quiet_watch_poll_period_v1','preflight':args.preflight,'constants':{'roi':[ROI_X,ROI_Y,ROI_W,ROI_H],'cue_ms':CUE_MS,'deadline_ms':DEADLINE_MS,'threshold':TARGET_THRESHOLD,'seed':21620260916},'records':records,'summary':summarize(records)}
    Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(payload['summary'],indent=2,sort_keys=True))
if __name__=='__main__': main()
