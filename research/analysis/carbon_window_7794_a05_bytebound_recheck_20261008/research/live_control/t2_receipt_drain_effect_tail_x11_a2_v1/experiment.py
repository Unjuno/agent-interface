#!/usr/bin/env python3
import argparse, hashlib, json, math, multiprocessing as mp, os, statistics, subprocess, sys, tempfile, threading, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

FRONTIER_MS=40.0
HOLD_MS=8.0
OFFSETS=[34.0,36.0,38.0,39.0]
APP_DELAYS=[0.0,3.0]
TARGET=(240,120)
SOURCE=(60,120)


def wait_until_ns(t):
    while True:
        now=time.perf_counter_ns(); rem=t-now
        if rem<=0: return now
        if rem>2_000_000: time.sleep((rem-1_000_000)/1e9)
        elif rem>100_000: time.sleep(rem/2e9)


def key_is_down(km,keycode):
    return bool(km[keycode//8] & (1 << (keycode%8)))


def pixel_raw(win,x,y):
    im=win.get_image(x,y,1,1,X.ZPixmap,0xffffffff)
    d=im.data
    if isinstance(d,str):
        return [ord(c) for c in d]
    return list(d)


def actuator(conn, display_name, xauth, window_id, hold_ms):
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth
    d=display.Display(display_name)
    win=d.create_resource_object('window',window_id)
    kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
    try:
        while True:
            msg=conn.recv()
            if msg.get('op')=='stop': break
            if msg.get('op')!='run': continue
            start=time.perf_counter_ns()
            win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
            down_call=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); down_ret=time.perf_counter_ns()
            time.sleep(hold_ms/1000.0)
            up_call=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); up_ret=time.perf_counter_ns()
            conn.send({'kind':'receipt','start_ns':start,'down_call_ns':down_call,'down_return_ns':down_ret,'up_call_ns':up_call,'up_return_ns':up_ret,'receipt_sent_ns':time.perf_counter_ns(),'keycode':kc})
    finally:
        d.close()


def observe(stop_evt, display_name, xauth, window_id, keycode, out):
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth
    d=display.Display(display_name); win=d.create_resource_object('window',window_id)
    initial_target=pixel_raw(win,*TARGET); initial_source=pixel_raw(win,*SOURCE)
    out['initial_target']=initial_target; out['initial_source']=initial_source
    samples=[]; effect_seen=None
    while not stop_evt.is_set():
        t0=time.perf_counter_ns()
        try:
            km=d.query_keymap(); down=key_is_down(km,keycode)
            pix=pixel_raw(win,*TARGET)
        except Exception as e:
            out['observer_error']=repr(e); break
        t1=time.perf_counter_ns()
        changed=(pix!=initial_target)
        if changed and effect_seen is None: effect_seen=(t0,t1)
        samples.append([t0,t1,down,changed])
        time.sleep(0.00025)
    out['samples']=samples; out['effect_seen_interval']=effect_seen
    try:
        out['final_target']=pixel_raw(win,*TARGET); out['final_source']=pixel_raw(win,*SOURCE); out['final_key_down']=key_is_down(d.query_keymap(),keycode)
    except Exception as e: out['final_error']=repr(e)
    d.close()


def derive_key_bounds(samples):
    # Each sample spans [t0,t1] and reports server state at query completion.
    # transition DOWN lies after last observed-up sample completion and at/before first down sample completion.
    first_down=next((i for i,s in enumerate(samples) if s[2]),None)
    if first_down is None: return None
    last_up_before=first_down-1 if first_down>0 else None
    first_up_after=next((i for i,s in enumerate(samples[first_down+1:],first_down+1) if not s[2]),None)
    if first_up_after is None: return None
    last_down=first_up_after-1
    down_lo=samples[last_up_before][1] if last_up_before is not None else samples[first_down][0]
    down_hi=samples[first_down][1]
    up_lo=samples[last_down][0]
    up_hi=samples[first_up_after][1]
    return {'down_lo_ns':down_lo,'down_hi_ns':down_hi,'up_lo_ns':up_lo,'up_hi_ns':up_hi,
            'guaranteed_occupancy_ns':max(0,up_lo-down_hi),'possible_occupancy_ns':max(0,up_hi-down_lo)}


def read_events(path):
    if not path.exists(): return []
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows


def run_case(root, idx, arm, offset_ms, app_delay_ms, display_name=':98'):
    case=root/f'case_{idx:04d}_{arm}_{int(offset_ms)}_{int(app_delay_ms)}'
    case.mkdir(parents=True,exist_ok=False)
    ready=case/'ready.json'; events=case/'events.jsonl'; stop=case/'stop'
    env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=str(root/'.Xauthority')
    fx=subprocess.Popen([sys.executable,str(root/'fixture.py'),'--ready',str(ready),'--events',str(events),'--delay-ms',str(app_delay_ms),'--stop',str(stop)],env=env,stdout=subprocess.DEVNULL,stderr=(case/'fixture.stderr').open('w'))
    deadline=time.time()+3
    while not ready.exists() and time.time()<deadline:
        if fx.poll() is not None: break
        time.sleep(0.01)
    if not ready.exists():
        raise RuntimeError(f'fixture_not_ready rc={fx.poll()} stderr={(case/"fixture.stderr").read_text(errors="replace")[:500]}')
    meta=json.loads(ready.read_text()); wid=int(meta['window_id'])
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=str(root/'.Xauthority')
    d=display.Display(display_name); win=d.create_resource_object('window',wid); kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
    win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
    parent,child=mp.Pipe(); proc=mp.Process(target=actuator,args=(child,display_name,str(root/'.Xauthority'),wid,HOLD_MS),daemon=True); proc.start()
    obs={}; stop_evt=threading.Event(); th=threading.Thread(target=observe,args=(stop_evt,display_name,str(root/'.Xauthority'),wid,kc,obs),daemon=True); th.start()
    time.sleep(0.01)
    t0=time.perf_counter_ns(); admit_target=t0+int(offset_ms*1e6); frontier_target=t0+int(FRONTIER_MS*1e6)
    wait_until_ns(admit_target); admit_send=time.perf_counter_ns(); parent.send({'op':'run'})
    wait_until_ns(frontier_target); frontier_return=time.perf_counter_ns()
    if arm=='IMMEDIATE_TRANSFER':
        handback_complete=frontier_return
        receipt=parent.recv(); receipt_recv=time.perf_counter_ns()
    elif arm=='ACTUATION_RECEIPT_DRAIN':
        receipt=parent.recv(); receipt_recv=time.perf_counter_ns(); handback_complete=receipt_recv
    else: raise ValueError(arm)
    # allow delayed app effect / observer to settle
    time.sleep(0.015)
    stop_evt.set(); th.join(timeout=1)
    stop.touch();
    try: fx.wait(timeout=1)
    except subprocess.TimeoutExpired: fx.terminate(); fx.wait(timeout=1)
    parent.send({'op':'stop'}); proc.join(timeout=1)
    if proc.is_alive(): proc.terminate(); proc.join()
    events_rows=read_events(events)
    bounds=derive_key_bounds(obs.get('samples',[]))
    effect_int=obs.get('effect_seen_interval')
    effect_first_hi=effect_int[1] if effect_int else None
    # Primary physical-occupancy bounds use the validated dual-edge XSync intervals (#981).
    # DOWN in [down_call, down_return], UP in [up_call, up_return].
    # Secondary sampled keymap bounds remain in `key_bounds` for corroboration only.
    key_possible_after = receipt['up_return_ns'] > handback_complete and receipt['down_call_ns'] < receipt['up_return_ns']
    key_guaranteed_after = receipt['up_call_ns'] > handback_complete and receipt['down_return_ns'] < receipt['up_call_ns']
    res={
        'case_id':idx,'arm':arm,'offset_ms':offset_ms,'app_delay_ms':app_delay_ms,
        't0_ns':t0,'admit_send_ns':admit_send,'frontier_return_ns':frontier_return,'handback_complete_ns':handback_complete,
        'receipt_recv_ns':receipt_recv,'receipt':receipt,'key_bounds':bounds,
        'physical_possible_after_handback':key_possible_after,'physical_guaranteed_after_handback':key_guaranteed_after,
        'effect_seen_interval':effect_int,'effect_after_handback': bool(effect_first_hi and effect_first_hi>handback_complete),
        'observer_initial_target':obs.get('initial_target'),'observer_final_target':obs.get('final_target'),
        'observer_initial_source':obs.get('initial_source'),'observer_final_source':obs.get('final_source'),
        'terminal_key_down':obs.get('final_key_down'),'observer_error':obs.get('observer_error'),'final_error':obs.get('final_error'),
        'events':events_rows,'fixture_rc':fx.returncode,'actuator_exitcode':proc.exitcode,
    }
    res['effect_correct']=res['observer_final_target']!=res['observer_initial_target'] and not res['terminal_key_down']
    res['local_completion_after_handback']=receipt['up_return_ns']>handback_complete
    (case/'result.json').write_text(json.dumps(res,indent=2,sort_keys=True),encoding='utf-8')
    d.close(); return res


def summarize(rows):
    by={a:[r for r in rows if r['arm']==a] for a in ['IMMEDIATE_TRANSFER','ACTUATION_RECEIPT_DRAIN']}
    def armstats(rs):
        return {
          'n':len(rs),
          'effect_correct':sum(r['effect_correct'] for r in rs),
          'terminal_released':sum(not r['terminal_key_down'] for r in rs),
          'local_completion_after_handback':sum(r['local_completion_after_handback'] for r in rs),
          'physical_possible_after_handback':sum(r['physical_possible_after_handback'] for r in rs),
          'physical_guaranteed_after_handback':sum(r['physical_guaranteed_after_handback'] for r in rs),
          'effect_after_handback':sum(r['effect_after_handback'] for r in rs),
          'handback_delay_ms_p50': statistics.median([(r['handback_complete_ns']-r['frontier_return_ns'])/1e6 for r in rs]) if rs else None,
          'handback_delay_ms_max': max([(r['handback_complete_ns']-r['frontier_return_ns'])/1e6 for r in rs],default=None)
        }
    s={a:armstats(rs) for a,rs in by.items()}
    b=s['IMMEDIATE_TRANSFER']; c=s['ACTUATION_RECEIPT_DRAIN']
    if all(r['effect_correct'] and not r['terminal_key_down'] and not r.get('observer_error') for r in rows):
        if (b['physical_possible_after_handback']+b['effect_after_handback'])<=0:
            disp='HOLD_NO_BASELINE_DISCRIMINATOR'
        elif c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['effect_after_handback']==0:
            disp='PASS_LIVE_RECEIPT_DRAIN_EFFECT_COVERAGE_SCOPED'
        elif c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['effect_after_handback']>0:
            disp='HOLD_EFFECT_TAIL_AFTER_ACTUATION_DRAIN'
        elif c['physical_possible_after_handback']>0:
            disp='FAIL_PHYSICAL_OCCUPANCY_OVERLAP'
        else: disp='FAIL_LIVE_TRANSFER'
    else: disp='FAIL_LIVE_TRANSFER'
    return {'arms':s,'disposition':disp}


def start_xvfb(root, display_name=':98'):
    xauth=root/'.Xauthority'; xauth.write_bytes(b'')
    env=os.environ.copy(); env['XAUTHORITY']=str(xauth)
    p=subprocess.Popen(['Xvfb',display_name,'-screen','0','320x240x24','-ac'],env=env,stdout=(root/'xvfb.out').open('w'),stderr=(root/'xvfb.err').open('w'))
    time.sleep(0.25)
    if p.poll() is not None: raise RuntimeError('Xvfb failed')
    return p


def run_plan(root, plan, outfile, index_offset=0):
    xv=start_xvfb(root)
    rows=[]
    try:
      for local_idx,(arm,off,delay) in enumerate(plan):
        idx=index_offset+local_idx
        rows.append(run_case(root,idx,arm,off,delay))
    finally:
      xv.terminate();
      try: xv.wait(timeout=1)
      except subprocess.TimeoutExpired: xv.kill(); xv.wait()
    result={'schema':1,'frontier_ms':FRONTIER_MS,'hold_ms':HOLD_MS,'rows':rows,'summary':summarize(rows)}
    Path(outfile).write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    return result


def construction_plan():
    # one matched pair at offset39 for each app delay; arm order counterbalanced
    return [('IMMEDIATE_TRANSFER',39.0,0.0),('ACTUATION_RECEIPT_DRAIN',39.0,0.0),('ACTUATION_RECEIPT_DRAIN',39.0,3.0),('IMMEDIATE_TRANSFER',39.0,3.0)]


def formal_plan():
    out=[]; pair=0
    for delay in APP_DELAYS:
      for off in OFFSETS:
       for rep in range(2):
        order=['IMMEDIATE_TRANSFER','ACTUATION_RECEIPT_DRAIN'] if pair%2==0 else ['ACTUATION_RECEIPT_DRAIN','IMMEDIATE_TRANSFER']
        for arm in order: out.append((arm,off,delay))
        pair+=1
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); ap.add_argument('--batch',type=int,choices=range(4))
    args=ap.parse_args(); root=Path(args.root); root.mkdir(parents=True,exist_ok=True)
    # copy fixture into execution root if needed
    src=Path(__file__).with_name('fixture.py'); dst=root/'fixture.py'
    if src.resolve()!=dst.resolve(): dst.write_bytes(src.read_bytes()); dst.chmod(0o755)
    if args.mode=='construction':
        plan=construction_plan(); offset=0
    else:
        full=formal_plan()
        if args.batch is None:
            plan=full; offset=0
        else:
            offset=args.batch*8; plan=full[offset:offset+8]
    res=run_plan(root,plan,args.out,index_offset=offset); print(json.dumps(res['summary'],indent=2,sort_keys=True))

if __name__=='__main__': main()
