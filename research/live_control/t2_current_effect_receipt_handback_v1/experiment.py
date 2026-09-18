#!/usr/bin/env python3
import argparse, hashlib, json, multiprocessing as mp, os, queue, statistics, subprocess, sys, threading, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest
FRONTIER_MS=40.0; HOLD_MS=8.0; OFFSETS=[34.0,36.0,38.0,39.0]; APP_DELAYS=[0.0,3.0]; TARGET=(240,120); SOURCE=(60,120)
ARMS=['ACTUATION_RECEIPT_DRAIN','CURRENT_EFFECT_RECEIPT_DRAIN']
def wait_until_ns(t):
    while True:
        now=time.perf_counter_ns(); rem=t-now
        if rem<=0: return now
        if rem>2_000_000: time.sleep((rem-1_000_000)/1e9)
        elif rem>100_000: time.sleep(rem/2e9)
def key_is_down(km,kc): return bool(km[kc//8] & (1 << (kc%8)))
def pixel_raw(win,x,y):
    im=win.get_image(x,y,1,1,X.ZPixmap,0xffffffff); d=im.data
    return [ord(c) for c in d] if isinstance(d,str) else list(d)
def hbytes(v): return hashlib.sha256(bytes(v)).hexdigest()
def validate_effect_receipt(receipt, *, window_id, generation, initial_hash):
    if not isinstance(receipt,dict): return False
    return (receipt.get('kind')=='current_effect_receipt' and receipt.get('window_id')==window_id and
            receipt.get('generation')==generation and receipt.get('initial_target_sha256')==initial_hash and
            receipt.get('changed') is True and isinstance(receipt.get('current_target_sha256'),str) and
            receipt.get('current_target_sha256')!=initial_hash and
            isinstance(receipt.get('observe_start_ns'),int) and isinstance(receipt.get('observe_end_ns'),int) and
            receipt['observe_start_ns']<=receipt['observe_end_ns'])
def actuator(conn, display_name, xauth, window_id, hold_ms):
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth; d=display.Display(display_name)
    win=d.create_resource_object('window',window_id); kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
    try:
        while True:
            msg=conn.recv()
            if msg.get('op')=='stop': break
            if msg.get('op')!='run': continue
            start=time.perf_counter_ns(); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
            dc=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); dr=time.perf_counter_ns(); time.sleep(hold_ms/1000)
            uc=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); ur=time.perf_counter_ns()
            conn.send({'kind':'actuation_receipt','start_ns':start,'down_call_ns':dc,'down_return_ns':dr,'up_call_ns':uc,'up_return_ns':ur,'receipt_sent_ns':time.perf_counter_ns(),'keycode':kc})
    finally: d.close()
def observe(stop_evt, display_name, xauth, window_id, keycode, generation, receipt_q, out):
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth; d=display.Display(display_name); win=d.create_resource_object('window',window_id)
    initial_target=pixel_raw(win,*TARGET); initial_source=pixel_raw(win,*SOURCE); ih=hbytes(initial_target)
    out['initial_target']=initial_target; out['initial_source']=initial_source; out['initial_target_sha256']=ih
    samples=[]; effect_seen=None; emitted=False
    while not stop_evt.is_set():
        t0=time.perf_counter_ns()
        try: km=d.query_keymap(); down=key_is_down(km,keycode); pix=pixel_raw(win,*TARGET)
        except Exception as e: out['observer_error']=repr(e); break
        t1=time.perf_counter_ns(); changed=(pix!=initial_target)
        if changed and effect_seen is None:
            effect_seen=(t0,t1)
            receipt={'kind':'current_effect_receipt','window_id':window_id,'generation':generation,'initial_target_sha256':ih,
                     'current_target_sha256':hbytes(pix),'observe_start_ns':t0,'observe_end_ns':t1,'changed':True,'grants_input_authority':False}
            receipt_q.put(receipt); out['effect_receipt']=receipt; emitted=True
        samples.append([t0,t1,down,changed]); time.sleep(0.00025)
    out['samples']=samples; out['effect_seen_interval']=effect_seen; out['effect_receipt_emitted']=emitted
    try: out['final_target']=pixel_raw(win,*TARGET); out['final_source']=pixel_raw(win,*SOURCE); out['final_key_down']=key_is_down(d.query_keymap(),keycode)
    except Exception as e: out['final_error']=repr(e)
    d.close()
def derive_key_bounds(samples):
    first_down=next((i for i,s in enumerate(samples) if s[2]),None)
    if first_down is None: return None
    last_up_before=first_down-1 if first_down>0 else None; first_up_after=next((i for i,s in enumerate(samples[first_down+1:],first_down+1) if not s[2]),None)
    if first_up_after is None: return None
    last_down=first_up_after-1; down_lo=samples[last_up_before][1] if last_up_before is not None else samples[first_down][0]; down_hi=samples[first_down][1]; up_lo=samples[last_down][0]; up_hi=samples[first_up_after][1]
    return {'down_lo_ns':down_lo,'down_hi_ns':down_hi,'up_lo_ns':up_lo,'up_hi_ns':up_hi,'guaranteed_occupancy_ns':max(0,up_lo-down_hi),'possible_occupancy_ns':max(0,up_hi-down_lo)}
def read_events(path):
    if not path.exists(): return []
    out=[]
    for line in path.read_text().splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out
def run_case(root, idx, arm, offset_ms, app_delay_ms, display_name=':98'):
    case=root/f'case_{idx:04d}_{arm}_{int(offset_ms)}_{int(app_delay_ms)}'; case.mkdir(parents=True,exist_ok=False)
    ready=case/'ready.json'; events=case/'events.jsonl'; stop=case/'stop'; env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=str(root/'.Xauthority')
    fx=subprocess.Popen([sys.executable,str(root/'fixture.py'),'--ready',str(ready),'--events',str(events),'--delay-ms',str(app_delay_ms),'--stop',str(stop)],env=env,stdout=subprocess.DEVNULL,stderr=(case/'fixture.stderr').open('w'))
    deadline=time.time()+3
    while not ready.exists() and time.time()<deadline:
        if fx.poll() is not None: break
        time.sleep(0.01)
    if not ready.exists(): raise RuntimeError('fixture_not_ready')
    wid=int(json.loads(ready.read_text())['window_id']); generation=idx+1
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=str(root/'.Xauthority'); d=display.Display(display_name); win=d.create_resource_object('window',wid); kc=d.keysym_to_keycode(XK.string_to_keysym('F8')); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
    parent,child=mp.Pipe(); proc=mp.Process(target=actuator,args=(child,display_name,str(root/'.Xauthority'),wid,HOLD_MS),daemon=True); proc.start()
    obs={}; q=queue.Queue(maxsize=1); stop_evt=threading.Event(); th=threading.Thread(target=observe,args=(stop_evt,display_name,str(root/'.Xauthority'),wid,kc,generation,q,obs),daemon=True); th.start(); time.sleep(0.01)
    deadline=time.time()+1
    while 'initial_target_sha256' not in obs and time.time()<deadline: time.sleep(0.0002)
    initial_hash=obs['initial_target_sha256']
    t0=time.perf_counter_ns(); wait_until_ns(t0+int(offset_ms*1e6)); admit_send=time.perf_counter_ns(); parent.send({'op':'run'}); wait_until_ns(t0+int(FRONTIER_MS*1e6)); frontier_return=time.perf_counter_ns()
    receipt=parent.recv(); receipt_recv=time.perf_counter_ns(); effect_receipt=None; effect_receipt_recv=None; effect_valid=None
    if arm=='ACTUATION_RECEIPT_DRAIN': handback_complete=receipt_recv
    elif arm=='CURRENT_EFFECT_RECEIPT_DRAIN':
        effect_receipt=q.get(timeout=1.0); effect_receipt_recv=time.perf_counter_ns(); effect_valid=validate_effect_receipt(effect_receipt,window_id=wid,generation=generation,initial_hash=initial_hash)
        if not effect_valid: raise RuntimeError('invalid_effect_receipt')
        handback_complete=effect_receipt_recv
    else: raise ValueError(arm)
    time.sleep(0.015); stop_evt.set(); th.join(timeout=1); stop.touch()
    try: fx.wait(timeout=1)
    except subprocess.TimeoutExpired: fx.terminate(); fx.wait(timeout=1)
    parent.send({'op':'stop'}); proc.join(timeout=1)
    if proc.is_alive(): proc.terminate(); proc.join()
    bounds=derive_key_bounds(obs.get('samples',[])); effect_int=obs.get('effect_seen_interval'); effect_hi=effect_int[1] if effect_int else None
    key_possible_after=receipt['up_return_ns']>handback_complete and receipt['down_call_ns']<receipt['up_return_ns']; key_guaranteed_after=receipt['up_call_ns']>handback_complete and receipt['down_return_ns']<receipt['up_call_ns']
    r={'case_id':idx,'arm':arm,'offset_ms':offset_ms,'app_delay_ms':app_delay_ms,'window_id':wid,'generation':generation,'initial_target_sha256':initial_hash,
       't0_ns':t0,'admit_send_ns':admit_send,'frontier_return_ns':frontier_return,'handback_complete_ns':handback_complete,'receipt_recv_ns':receipt_recv,'receipt':receipt,
       'effect_receipt':effect_receipt,'effect_receipt_recv_ns':effect_receipt_recv,'effect_receipt_valid':effect_valid,'key_bounds':bounds,
       'physical_possible_after_handback':key_possible_after,'physical_guaranteed_after_handback':key_guaranteed_after,'effect_seen_interval':effect_int,
       'effect_after_handback':bool(effect_hi and effect_hi>handback_complete),'observer_initial_target':obs.get('initial_target'),'observer_final_target':obs.get('final_target'),
       'terminal_key_down':obs.get('final_key_down'),'observer_error':obs.get('observer_error'),'final_error':obs.get('final_error'),'events':read_events(events),'fixture_rc':fx.returncode,'actuator_exitcode':proc.exitcode}
    r['effect_correct']=r['observer_final_target']!=r['observer_initial_target'] and not r['terminal_key_down']; r['local_completion_after_handback']=receipt['up_return_ns']>handback_complete
    r['handback_delay_ms']=(handback_complete-frontier_return)/1e6; r['extra_wait_after_actuation_receipt_ms']=(handback_complete-receipt_recv)/1e6
    (case/'result.json').write_text(json.dumps(r,indent=2,sort_keys=True)); d.close(); return r
def directed_controls():
    base={'kind':'current_effect_receipt','window_id':7,'generation':9,'initial_target_sha256':'a'*64,'current_target_sha256':'b'*64,'observe_start_ns':10,'observe_end_ns':11,'changed':True,'grants_input_authority':False}
    ok=validate_effect_receipt(base,window_id=7,generation=9,initial_hash='a'*64); stale=dict(base,generation=8); wrong=dict(base,initial_target_sha256='c'*64)
    return {'valid_accept':ok,'stale_generation_rejected':not validate_effect_receipt(stale,window_id=7,generation=9,initial_hash='a'*64),'mismatched_source_rejected':not validate_effect_receipt(wrong,window_id=7,generation=9,initial_hash='a'*64)}
def summarize(rows):
    by={a:[r for r in rows if r['arm']==a] for a in ARMS}
    def stats(rs):
        waits=[r['extra_wait_after_actuation_receipt_ms'] for r in rs]
        return {'n':len(rs),'effect_correct':sum(r['effect_correct'] for r in rs),'terminal_released':sum(not r['terminal_key_down'] for r in rs),'local_completion_after_handback':sum(r['local_completion_after_handback'] for r in rs),'physical_possible_after_handback':sum(r['physical_possible_after_handback'] for r in rs),'physical_guaranteed_after_handback':sum(r['physical_guaranteed_after_handback'] for r in rs),'effect_after_handback':sum(r['effect_after_handback'] for r in rs),'effect_receipt_valid':sum(r.get('effect_receipt_valid') is True for r in rs),'handback_delay_ms_max':max([r['handback_delay_ms'] for r in rs],default=None),'extra_wait_after_actuation_receipt_ms_max':max(waits,default=None),'extra_wait_after_actuation_receipt_ms_p50':statistics.median(waits) if waits else None}
    s={a:stats(rs) for a,rs in by.items()}; b=s[ARMS[0]]; c=s[ARMS[1]]
    allgood=all(r['effect_correct'] and not r['terminal_key_down'] and not r.get('observer_error') and not r.get('final_error') for r in rows)
    if not allgood: disp='FAIL_LIVE_TRANSFER'
    elif b['effect_after_handback']<=0: disp='HOLD_NO_BASELINE_DISCRIMINATOR'
    elif c['physical_possible_after_handback']>0: disp='FAIL_PHYSICAL_OCCUPANCY_OVERLAP'
    elif c['effect_receipt_valid']!=c['n']: disp='FAIL_EFFECT_RECEIPT_CURRENTNESS'
    elif c['effect_after_handback']>0: disp='FAIL_EFFECT_RECEIPT_NOT_SUFFICIENT'
    elif c['extra_wait_after_actuation_receipt_ms_max'] is not None and c['extra_wait_after_actuation_receipt_ms_max']>=10.0: disp='HOLD_EFFECT_HANDOFF_TOO_SLOW'
    elif c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['physical_guaranteed_after_handback']==0: disp='PASS_CURRENT_EFFECT_RECEIPT_HANDBACK_SCOPED'
    else: disp='FAIL_LIVE_TRANSFER'
    return {'arms':s,'disposition':disp}
def start_xvfb(root, display_name=':98'):
    xauth=root/'.Xauthority'; xauth.write_bytes(b''); env=os.environ.copy(); env['XAUTHORITY']=str(xauth)
    p=subprocess.Popen(['Xvfb',display_name,'-screen','0','320x240x24','-ac'],env=env,stdout=(root/'xvfb.out').open('w'),stderr=(root/'xvfb.err').open('w')); time.sleep(0.25)
    if p.poll() is not None: raise RuntimeError('Xvfb failed')
    return p
def run_plan(root, plan, outfile, index_offset=0, controls=False):
    xv=start_xvfb(root); rows=[]
    try:
        for j,(arm,off,delay) in enumerate(plan): rows.append(run_case(root,index_offset+j,arm,off,delay))
    finally:
        xv.terminate()
        try: xv.wait(timeout=1)
        except subprocess.TimeoutExpired: xv.kill(); xv.wait()
    out={'schema':1,'frontier_ms':FRONTIER_MS,'hold_ms':HOLD_MS,'rows':rows,'summary':summarize(rows)}
    if controls: out['directed_controls']=directed_controls()
    Path(outfile).write_text(json.dumps(out,indent=2,sort_keys=True)); return out
def construction_plan(): return [(ARMS[0],39,0),(ARMS[1],39,0),(ARMS[1],39,3),(ARMS[0],39,3)]
def formal_plan():
    out=[]; pair=0
    for delay in APP_DELAYS:
      for off in OFFSETS:
       for rep in range(2):
        order=ARMS if pair%2==0 else list(reversed(ARMS)); out.extend((arm,off,delay) for arm in order); pair+=1
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); ap.add_argument('--batch',type=int,choices=range(4)); args=ap.parse_args(); root=Path(args.root); root.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).with_name('fixture.py'); dst=root/'fixture.py'
    if src.resolve()!=dst.resolve(): dst.write_bytes(src.read_bytes()); dst.chmod(0o755)
    if args.mode=='construction': plan=construction_plan(); offset=0; controls=True
    else:
        full=formal_plan(); offset=(args.batch or 0)*8 if args.batch is not None else 0; plan=full[offset:offset+8] if args.batch is not None else full; controls=False
    r=run_plan(root,plan,args.out,offset,controls); print(json.dumps(r['summary'],indent=2,sort_keys=True))
if __name__=='__main__': main()
