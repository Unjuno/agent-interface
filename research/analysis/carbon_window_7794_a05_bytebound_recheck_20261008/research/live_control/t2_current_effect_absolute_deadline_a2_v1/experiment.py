#!/usr/bin/env python3
import argparse, json, math, multiprocessing as mp, os, queue, statistics, subprocess, sys, threading, time, uuid
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest
FRONTIER_MS=40.0; HOLD_MS=8.0; EFFECT_TIMEOUT_MS=8.0
OFFSETS=[34.0,36.0,38.0,39.0]; APP_DELAYS=[0.0,3.0]; TARGET=(240,120); SOURCE=(60,120)
BASE='ACTUATION_RECEIPT_DRAIN'; CAND='CURRENT_EFFECT_RECEIPT_DRAIN'
def wait_until_ns(t):
 while True:
  now=time.perf_counter_ns(); rem=t-now
  if rem<=0: return now
  if rem>2_000_000: time.sleep((rem-1_000_000)/1e9)
  elif rem>100_000: time.sleep(rem/2e9)
def key_is_down(km,k): return bool(km[k//8] & (1 << (k%8)))
def pixel_raw(win,x,y):
 d=win.get_image(x,y,1,1,X.ZPixmap,0xffffffff).data
 return [ord(c) for c in d] if isinstance(d,str) else list(d)
def actuator(conn,display_name,xauth,window_id,hold_ms,request_id):
 os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth
 d=display.Display(display_name); win=d.create_resource_object('window',window_id); kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
 try:
  while True:
   msg=conn.recv()
   if msg.get('op')=='stop': break
   if msg.get('op')!='run': continue
   win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
   down_call=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); down_ret=time.perf_counter_ns(); time.sleep(hold_ms/1000)
   up_call=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); up_ret=time.perf_counter_ns()
   conn.send({'kind':'ACTUATION_RECEIPT','request_id':request_id,'down_call_ns':down_call,'down_return_ns':down_ret,'up_call_ns':up_call,'up_return_ns':up_ret,'receipt_sent_ns':time.perf_counter_ns(),'keycode':kc})
 finally: d.close()
def observe(stop_evt,display_name,xauth,window_id,keycode,out,effect_q,session_id,request_id):
 os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=xauth
 d=display.Display(display_name); win=d.create_resource_object('window',window_id)
 initial_target=pixel_raw(win,*TARGET); initial_source=pixel_raw(win,*SOURCE); out['initial_target']=initial_target; out['initial_source']=initial_source
 samples=[]; seq=0; receipt=None
 while not stop_evt.is_set():
  t0=time.perf_counter_ns()
  try: km=d.query_keymap(); down=key_is_down(km,keycode); pix=pixel_raw(win,*TARGET)
  except Exception as e: out['observer_error']=repr(e); break
  t1=time.perf_counter_ns(); changed=(pix!=initial_target); seq+=1; samples.append([t0,t1,down,changed])
  if changed and receipt is None:
   receipt={'kind':'OBSERVATION_RECEIPT','role':'CURRENT_EFFECT','session_id':session_id,'request_id':request_id,'observer_seq':seq,'observed_lo_ns':t0,'observed_hi_ns':t1,'input_authority':False,'semantic_authority':False}
   out['effect_receipt']=receipt; effect_q.put(receipt)
  time.sleep(0.00025)
 out['samples']=samples
 try: out['final_target']=pixel_raw(win,*TARGET); out['final_source']=pixel_raw(win,*SOURCE); out['final_key_down']=key_is_down(d.query_keymap(),keycode)
 except Exception as e: out['final_error']=repr(e)
 d.close()
def read_events(path):
 if not path.exists(): return []
 out=[]
 for line in path.read_text().splitlines():
  try: out.append(json.loads(line))
  except Exception: pass
 return out
def start_xvfb(root,display_name=':98'):
 xauth=root/'.Xauthority'; xauth.write_bytes(b''); env=os.environ.copy(); env['XAUTHORITY']=str(xauth)
 p=subprocess.Popen(['Xvfb',display_name,'-screen','0','320x240x24','-ac'],env=env,stdout=(root/'xvfb.out').open('w'),stderr=(root/'xvfb.err').open('w')); time.sleep(.25)
 if p.poll() is not None: raise RuntimeError('Xvfb_failed')
 return p
def wait_effect(q,deadline_ns,session_id,request_id):
 while True:
  now=time.perf_counter_ns(); rem=(deadline_ns-now)/1e9
  if rem<=0: return None,now
  try: r=q.get(timeout=rem)
  except queue.Empty: return None,time.perf_counter_ns()
  wake_ns=time.perf_counter_ns()
  if wake_ns>=deadline_ns: return None,wake_ns
  if r.get('session_id')==session_id and r.get('request_id')==request_id and r.get('role')=='CURRENT_EFFECT': return r,wake_ns
def run_case(root,idx,arm,offset_ms,app_delay_ms,effect_enabled=True,display_name=':98'):
 case=root/f'case_{idx:04d}_{arm}_{int(offset_ms)}_{int(app_delay_ms)}_{int(effect_enabled)}'; case.mkdir(parents=True,exist_ok=False)
 session_id=f's{idx}-{uuid.uuid4().hex[:12]}'; request_id=f'r{idx}-{uuid.uuid4().hex[:12]}'
 ready=case/'ready.json'; events=case/'events.jsonl'; stop=case/'stop'; env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=str(root/'.Xauthority')
 fx=subprocess.Popen([sys.executable,str(root/'fixture.py'),'--ready',str(ready),'--events',str(events),'--delay-ms',str(app_delay_ms),'--stop',str(stop),'--effect-enabled','1' if effect_enabled else '0'],env=env,stdout=subprocess.DEVNULL,stderr=(case/'fixture.stderr').open('w'))
 deadline=time.time()+3
 while not ready.exists() and time.time()<deadline:
  if fx.poll() is not None: break
  time.sleep(.01)
 if not ready.exists(): raise RuntimeError('fixture_not_ready:'+ (case/'fixture.stderr').read_text(errors='replace')[:500])
 wid=int(json.loads(ready.read_text())['window_id']); os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=str(root/'.Xauthority')
 d=display.Display(display_name); win=d.create_resource_object('window',wid); kc=d.keysym_to_keycode(XK.string_to_keysym('F8')); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
 parent,child=mp.Pipe(); proc=mp.Process(target=actuator,args=(child,display_name,str(root/'.Xauthority'),wid,HOLD_MS,request_id),daemon=True); proc.start()
 obs={}; q=queue.Queue(); stop_evt=threading.Event(); th=threading.Thread(target=observe,args=(stop_evt,display_name,str(root/'.Xauthority'),wid,kc,obs,q,session_id,request_id),daemon=True); th.start(); time.sleep(.01)
 t0=time.perf_counter_ns(); wait_until_ns(t0+int(offset_ms*1e6)); admit_ns=time.perf_counter_ns(); parent.send({'op':'run'}); wait_until_ns(t0+int(FRONTIER_MS*1e6)); frontier_ns=time.perf_counter_ns()
 act=parent.recv(); act_recv=time.perf_counter_ns()
 handback=None; status='COMPLETED'; accepted=None; effect_accept_ns=None; effect_deadline_ns=None
 if arm==BASE: handback=act_recv
 elif arm==CAND:
  effect_deadline_ns=act_recv+int(EFFECT_TIMEOUT_MS*1e6)
  accepted,effect_accept_ns=wait_effect(q,effect_deadline_ns,session_id,request_id)
  if accepted is None: status='UNRESOLVED_EFFECT_TIMEOUT'
  else: handback=effect_accept_ns
 else: raise ValueError(arm)
 time.sleep(.012); stop_evt.set(); th.join(timeout=1); stop.touch()
 try: fx.wait(timeout=1)
 except subprocess.TimeoutExpired: fx.terminate(); fx.wait(timeout=1)
 parent.send({'op':'stop'}); proc.join(timeout=1)
 if proc.is_alive(): proc.terminate(); proc.join()
 ev=read_events(events); effect_receipt=obs.get('effect_receipt'); final_changed=obs.get('final_target')!=obs.get('initial_target')
 expected_correct=(final_changed if effect_enabled else not final_changed) and not obs.get('final_key_down',True)
 effect_after=(bool(effect_receipt and handback is not None and effect_receipt['observed_hi_ns']>handback))
 res={'case_id':idx,'arm':arm,'offset_ms':offset_ms,'app_delay_ms':app_delay_ms,'effect_enabled':effect_enabled,'session_id':session_id,'request_id':request_id,'t0_ns':t0,'admit_ns':admit_ns,'frontier_return_ns':frontier_ns,'actuation_receipt':act,'actuation_receipt_recv_ns':act_recv,'effect_receipt':effect_receipt,'accepted_effect_receipt':accepted,'effect_deadline_ns':effect_deadline_ns,'effect_accept_ns':effect_accept_ns,'handback_complete_ns':handback,'handback_status':status,'effect_after_handback':effect_after,'effect_correct':expected_correct,'terminal_key_down':obs.get('final_key_down'),'observer_error':obs.get('observer_error'),'final_error':obs.get('final_error'),'events':ev,'fixture_rc':fx.returncode,'actuator_exitcode':proc.exitcode}
 res['local_completion_after_handback']= bool(handback is not None and act['up_return_ns']>handback)
 res['physical_possible_after_handback']= bool(handback is not None and act['up_return_ns']>handback and act['down_call_ns']<act['up_return_ns'])
 res['effect_receipt_wait_ms']= ((handback-act_recv)/1e6 if arm==CAND and handback is not None else None)
 (case/'result.json').write_text(json.dumps(res,indent=2,sort_keys=True)); d.close(); return res
def p95(xs):
 s=sorted(xs); return s[max(0,math.ceil(.95*len(s))-1)] if s else None
def summarize(pos,ctrl):
 by={a:[r for r in pos if r['arm']==a] for a in [BASE,CAND]}
 b,c=by[BASE],by[CAND]; waits=[r['effect_receipt_wait_ms'] for r in c if r['effect_receipt_wait_ms'] is not None]
 late_accepted=sum(bool(r.get('accepted_effect_receipt') and r.get('effect_accept_ns') is not None and r.get('effect_deadline_ns') is not None and r['effect_accept_ns']>=r['effect_deadline_ns']) for r in c)
 summary={'positive':{BASE:{'n':len(b),'effect_after_handback':sum(r['effect_after_handback'] for r in b),'correct':sum(r['effect_correct'] for r in b),'terminal_released':sum(not r['terminal_key_down'] for r in b)},CAND:{'n':len(c),'effect_after_handback':sum(r['effect_after_handback'] for r in c),'correct':sum(r['effect_correct'] for r in c),'terminal_released':sum(not r['terminal_key_down'] for r in c),'local_completion_after_handback':sum(r['local_completion_after_handback'] for r in c),'physical_possible_after_handback':sum(r['physical_possible_after_handback'] for r in c),'effect_receipts':sum(r['effect_receipt'] is not None for r in c),'handback_completed':sum(r['handback_status']=='COMPLETED' for r in c),'positive_timeouts':sum(r['handback_status']=='UNRESOLVED_EFFECT_TIMEOUT' for r in c),'late_accepted':late_accepted,'wait_p95_ms':p95(waits),'wait_max_ms':max(waits,default=None)},},'controls':{'n':len(ctrl),'effect_receipts':sum(r['effect_receipt'] is not None for r in ctrl),'completed_handbacks':sum(r['handback_status']=='COMPLETED' for r in ctrl),'unresolved_timeouts':sum(r['handback_status']=='UNRESOLVED_EFFECT_TIMEOUT' for r in ctrl),'terminal_released':sum(not r['terminal_key_down'] for r in ctrl),'correct':sum(r['effect_correct'] for r in ctrl)}}
 cc=summary['positive'][CAND]; ct=summary['controls']
 if all(r['effect_correct'] and not r['terminal_key_down'] and not r.get('observer_error') for r in pos+ctrl):
  lineage=all((r['effect_receipt'] is None) or (r['effect_receipt']['session_id']==r['session_id'] and r['effect_receipt']['request_id']==r['request_id'] and r['effect_receipt']['role']=='CURRENT_EFFECT' and not r['effect_receipt']['input_authority'] and not r['effect_receipt']['semantic_authority']) for r in c)
  if cc['late_accepted']>0: disp='FAIL_LATE_RECEIPT_ACCEPTED'
  elif cc['effect_after_handback']>0: disp='FAIL_EFFECT_RECEIPT_COVERAGE'
  elif ct['effect_receipts']>0 or ct['completed_handbacks']>0: disp='FAIL_EFFECT_RECEIPT_FALSE_POSITIVE'
  elif not lineage: disp='FAIL_LIVE_TRANSFER'
  elif cc['local_completion_after_handback'] or cc['physical_possible_after_handback']: disp='FAIL_LIVE_TRANSFER'
  elif summary['positive'][BASE]['effect_after_handback']<=0: disp='HOLD_NO_BASELINE_DISCRIMINATOR'
  elif ct['unresolved_timeouts']!=len(ctrl): disp='FAIL_EFFECT_RECEIPT_FALSE_POSITIVE'
  elif cc['positive_timeouts']>0: disp='HOLD_POSITIVE_EFFECT_TIMEOUT_WITH_SAFE_DEADLINE'
  elif cc['effect_receipts']!=len(c) or cc['handback_completed']!=len(c): disp='FAIL_LIVE_TRANSFER'
  elif cc['wait_p95_ms']>=6 or cc['wait_max_ms']>=8: disp='HOLD_EFFECT_RECEIPT_TOO_SLOW'
  else: disp='PASS_CURRENT_EFFECT_ABSOLUTE_DEADLINE_SCOPED'
 else: disp='FAIL_LIVE_TRANSFER'
 summary['disposition']=disp; return summary
def positive_plan():
 out=[]; pair=0
 for delay in APP_DELAYS:
  for off in OFFSETS:
   for rep in range(2):
    order=[BASE,CAND] if pair%2==0 else [CAND,BASE]
    out.extend((a,off,delay,True) for a in order); pair+=1
 return out
def construction_plan(): return [(BASE,39,0,True),(CAND,39,0,True),(CAND,39,3,True),(BASE,39,3,True),(CAND,39,0,False)]
def control_plan(): return [(CAND,o,0,False) for o in OFFSETS]
def run_plan(root,plan,outfile,index_offset):
 xv=start_xvfb(root); rows=[]
 try:
  for i,args in enumerate(plan): rows.append(run_case(root,index_offset+i,*args))
 finally:
  xv.terminate();
  try: xv.wait(timeout=1)
  except subprocess.TimeoutExpired: xv.kill(); xv.wait()
 Path(outfile).write_text(json.dumps({'schema':1,'rows':rows},indent=2,sort_keys=True)); return rows
def main():
 p=argparse.ArgumentParser(); p.add_argument('mode',choices=['construction','formal-positive','formal-controls']); p.add_argument('--root',required=True); p.add_argument('--out',required=True); p.add_argument('--batch',type=int,choices=range(4)); a=p.parse_args(); root=Path(a.root); root.mkdir(parents=True,exist_ok=True); src=Path(__file__).with_name('fixture.py'); dst=root/'fixture.py'; dst.write_bytes(src.read_bytes()); dst.chmod(0o755)
 if a.mode=='construction': rows=run_plan(root,construction_plan(),a.out,0); pos=rows[:4]; ctrl=rows[4:]
 elif a.mode=='formal-positive':
  if a.batch is None: raise SystemExit('batch required')
  full=positive_plan(); off=a.batch*8; rows=run_plan(root,full[off:off+8],a.out,off); pos=rows; ctrl=[]
 else: rows=run_plan(root,control_plan(),a.out,32); pos=[]; ctrl=rows
 print(json.dumps({'rows':len(rows),'positive_summary':summarize(pos,ctrl) if (pos and ctrl) else None},sort_keys=True))
if __name__=='__main__': main()
