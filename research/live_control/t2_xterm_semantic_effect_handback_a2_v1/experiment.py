#!/usr/bin/env python3
import argparse,json,math,multiprocessing as mp,os,queue,subprocess,sys,threading,time,uuid
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
FRONTIER_MS=40.0; HOLD_MS=8.0; EFFECT_TIMEOUT_MS=8.0
OFFSETS=[34.0,36.0,38.0,39.0]; DELAYS=[10.0,13.0]
BASE='ACTUATION_RECEIPT_DRAIN'; CAND='SEMANTIC_EFFECT_RECEIPT_DRAIN'
def wait_until_ns(t):
 while True:
  n=time.perf_counter_ns(); r=t-n
  if r<=0:return n
  if r>2_000_000:time.sleep((r-1_000_000)/1e9)
  elif r>100_000:time.sleep(r/2e9)
def key_down(km,k):return bool(km[k//8]&(1<<(k%8)))
def walk(w):
 out=[]; stack=[w]
 while stack:
  q=stack.pop();
  try: out.append(q); stack.extend(q.query_tree().children)
  except Exception: pass
 return out
def find_top(d,title,timeout=3):
 end=time.time()+timeout;root=d.screen().root
 while time.time()<end:
  for w in walk(root):
   try:
    if w.get_wm_name()==title:return w
   except Exception:pass
  time.sleep(.01)
 raise RuntimeError('xterm_top_not_found')
def wait_json(path,timeout=3):
 end=time.time()+timeout
 while time.time()<end:
  if path.exists():
   try:return json.loads(path.read_text())
   except Exception:pass
  time.sleep(.0005)
 return None
def actuator(conn,name,wid,request):
 d=display.Display(name);w=d.create_resource_object('window',wid);kc=d.keysym_to_keycode(XK.string_to_keysym('x'))
 try:
  m=conn.recv();assert m['op']=='run'; w.set_input_focus(X.RevertToPointerRoot,X.CurrentTime);d.sync(); f=d.get_input_focus();fid=getattr(f.focus,'id',f.focus)
  dc=time.perf_counter_ns();xtest.fake_input(d,X.KeyPress,kc);d.sync();dr=time.perf_counter_ns();time.sleep(HOLD_MS/1000);uc=time.perf_counter_ns();xtest.fake_input(d,X.KeyRelease,kc);d.sync();ur=time.perf_counter_ns();conn.send({'kind':'ACTUATION_RECEIPT','request_id':request,'focus_id':fid,'target_id':wid,'down_call_ns':dc,'down_return_ns':dr,'up_call_ns':uc,'up_return_ns':ur,'keycode':kc})
 finally:d.close()
def monitor(stop,path,q,out):
 seen=False
 while not stop.is_set():
  if path.exists() and not seen:
   try:r=json.loads(path.read_text());out['receipt']=r;q.put(r);seen=True
   except Exception as e:out['error']=repr(e)
  time.sleep(.00025)
def wait_effect(q,deadline,session,request):
 while True:
  n=time.perf_counter_ns();rem=(deadline-n)/1e9
  if rem<=0:return None,n
  try:r=q.get(timeout=rem)
  except queue.Empty:return None,time.perf_counter_ns()
  wake=time.perf_counter_ns()
  if wake>=deadline:return None,wake
  if r.get('session_id')==session and r.get('request_id')==request and r.get('role')=='TASK_SEMANTIC_EFFECT':return r,wake
def start_xvfb(root,name=':95'):
 x=root/'.Xauthority';x.write_bytes(b'');os.environ['DISPLAY']=name;os.environ['XAUTHORITY']=str(x);env=os.environ.copy();p=subprocess.Popen(['Xvfb',name,'-screen','0','640x360x24','-ac'],env=env,stdout=(root/'xvfb.out').open('w'),stderr=(root/'xvfb.err').open('w'));time.sleep(.2)
 if p.poll() is not None:raise RuntimeError('xvfb_failed')
 return p
def run_case(root,idx,arm,offset,delay,effect=True,name=':95'):
 case=root/f'case_{idx:04d}';case.mkdir();session=f's{idx}-{uuid.uuid4().hex[:10]}';request=f'r{idx}-{uuid.uuid4().hex[:10]}';ready=case/'ready.json';receipt=case/'receipt.json';title=f'AI1543-{idx}-{uuid.uuid4().hex[:8]}';env=os.environ.copy();env['DISPLAY']=name
 xp=subprocess.Popen(['xterm','-T',title,'-geometry','40x10+0+0','-e',sys.executable,str(Path(__file__).with_name('task_helper.py')),'--ready',str(ready),'--receipt',str(receipt),'--session',session,'--request',request,'--delay-ms',str(delay),'--effect-enabled','1' if effect else '0'],env=env,stdout=(case/'xterm.out').open('w'),stderr=(case/'xterm.err').open('w'))
 d=display.Display(name);top=find_top(d,title);rdy=wait_json(ready,3)
 if not rdy:xp.terminate();xp.wait();d.close();raise RuntimeError('helper_not_ready')
 top.set_input_focus(X.RevertToPointerRoot,X.CurrentTime);d.sync();pre=d.get_input_focus();preid=getattr(pre.focus,'id',pre.focus)
 q=queue.Queue();mo={};st=threading.Event();th=threading.Thread(target=monitor,args=(st,receipt,q,mo),daemon=True);th.start();par,ch=mp.Pipe();proc=mp.Process(target=actuator,args=(ch,name,top.id,request),daemon=True);proc.start();t0=time.perf_counter_ns();wait_until_ns(t0+int(offset*1e6));par.send({'op':'run'});wait_until_ns(t0+int(FRONTIER_MS*1e6));front=time.perf_counter_ns();act=par.recv();ar=time.perf_counter_ns();accepted=None;acc=None;deadline=None;status='COMPLETED'
 if arm==BASE:hand=ar
 else:
  deadline=ar+int(EFFECT_TIMEOUT_MS*1e6);accepted,acc=wait_effect(q,deadline,session,request)
  if accepted is None:hand=None;status='UNRESOLVED_EFFECT_TIMEOUT'
  else:hand=acc
 time.sleep(.02);st.set();th.join(timeout=1);final=mo.get('receipt') or (wait_json(receipt,.01) if receipt.exists() else None)
 try:rc=xp.wait(timeout=1)
 except subprocess.TimeoutExpired:xp.terminate();rc=xp.wait(timeout=1)
 proc.join(timeout=1)
 if proc.is_alive():proc.terminate();proc.join()
 kc=d.keysym_to_keycode(XK.string_to_keysym('x'));down=key_down(d.query_keymap(),kc);d.close(); valid=bool(final and final.get('session_id')==session and final.get('request_id')==request and final.get('role')=='TASK_SEMANTIC_EFFECT' and final.get('accepted_key')=='x' and final.get('result')=='TOKEN_ACCEPTED' and final.get('input_authority') is False and final.get('semantic_authority') is False);correct=(valid if effect else final is None) and not down and rc==0 and preid==top.id and act.get('focus_id')==top.id
 eff=final.get('effect_ns') if final else None;r={'case_id':idx,'arm':arm,'offset_ms':offset,'semantic_delay_ms':delay,'effect_enabled':effect,'session_id':session,'request_id':request,'ready_ns':rdy.get('ready_ns'),'window_id':top.id,'pre_focus_id':preid,'frontier_return_ns':front,'actuation_receipt':act,'actuation_receipt_recv_ns':ar,'semantic_receipt':final,'accepted_semantic_receipt':accepted,'semantic_receipt_valid':valid,'effect_deadline_ns':deadline,'effect_accept_ns':acc,'handback_complete_ns':hand,'handback_status':status,'semantic_effect_after_handback':bool(eff and hand is not None and eff>hand),'local_completion_after_handback':bool(hand is not None and act['up_return_ns']>hand),'physical_possible_after_handback':bool(hand is not None and act['up_return_ns']>hand),'late_accepted':bool(accepted and acc>=deadline),'receipt_wait_ms':((hand-ar)/1e6 if arm==CAND and hand is not None else None),'terminal_key_down':down,'task_correct':correct,'xterm_rc':rc,'actuator_exitcode':proc.exitcode,'monitor_error':mo.get('error')};(case/'result.json').write_text(json.dumps(r,indent=2,sort_keys=True));return r
def p95(xs):
 s=sorted(xs);return s[max(0,math.ceil(.95*len(s))-1)] if s else None
def summarize(pos,ctrl):
 b=[x for x in pos if x['arm']==BASE];c=[x for x in pos if x['arm']==CAND];w=[x['receipt_wait_ms'] for x in c if x['receipt_wait_ms'] is not None];out={'positive':{BASE:{'n':len(b),'effect_after_handback':sum(x['semantic_effect_after_handback'] for x in b),'correct':sum(x['task_correct'] for x in b),'released':sum(not x['terminal_key_down'] for x in b)},CAND:{'n':len(c),'effect_after_handback':sum(x['semantic_effect_after_handback'] for x in c),'correct':sum(x['task_correct'] for x in c),'released':sum(not x['terminal_key_down'] for x in c),'valid_receipts':sum(x['semantic_receipt_valid'] for x in c),'completed_handbacks':sum(x['handback_status']=='COMPLETED' for x in c),'timeouts':sum(x['handback_status']!='COMPLETED' for x in c),'late_accepted':sum(x['late_accepted'] for x in c),'local_completion_after_handback':sum(x['local_completion_after_handback'] for x in c),'physical_possible_after_handback':sum(x['physical_possible_after_handback'] for x in c),'wait_p95_ms':p95(w),'wait_max_ms':max(w,default=None)}},'controls':{'n':len(ctrl),'receipts':sum(x['semantic_receipt'] is not None for x in ctrl),'completed_handbacks':sum(x['handback_status']=='COMPLETED' for x in ctrl),'timeouts':sum(x['handback_status']!='COMPLETED' for x in ctrl),'correct':sum(x['task_correct'] for x in ctrl),'released':sum(not x['terminal_key_down'] for x in ctrl)}};cc=out['positive'][CAND];ct=out['controls']
 if not all(x['task_correct'] and not x['terminal_key_down'] and x['xterm_rc']==0 for x in pos+ctrl):disp='FAIL_XTERM_DELIVERY_REGRESSION'
 elif cc['late_accepted']:disp='FAIL_LATE_RECEIPT_ACCEPTED'
 elif cc['effect_after_handback']:disp='FAIL_SEMANTIC_RECEIPT_LINEAGE'
 elif ct['receipts'] or ct['completed_handbacks']:disp='FAIL_SEMANTIC_RECEIPT_FALSE_POSITIVE'
 elif out['positive'][BASE]['effect_after_handback']==0:disp='HOLD_NO_XTERM_SEMANTIC_DISCRIMINATOR'
 elif cc['local_completion_after_handback'] or cc['physical_possible_after_handback']:disp='FAIL_LIVE_TRANSFER'
 elif cc['timeouts']:disp='HOLD_XTERM_SEMANTIC_EFFECT_TIMEOUT_WITH_SAFE_DEADLINE'
 elif cc['valid_receipts']!=len(c):disp='FAIL_SEMANTIC_RECEIPT_LINEAGE'
 elif cc['wait_p95_ms']>=6 or cc['wait_max_ms']>=8:disp='HOLD_XTERM_SEMANTIC_EFFECT_TIMEOUT_WITH_SAFE_DEADLINE'
 elif ct['timeouts']!=len(ctrl):disp='FAIL_SEMANTIC_RECEIPT_FALSE_POSITIVE'
 else:disp='PASS_XTERM_SEMANTIC_EFFECT_HANDBACK_A2_SCOPED'
 out['disposition']=disp;return out
def construction_plan():return [(BASE,39,10,True),(CAND,39,10,True),(CAND,39,13,True),(BASE,39,13,True),(CAND,39,10,False)]
def positive_plan():
 out=[];pair=0
 for delay in DELAYS:
  for off in OFFSETS:
   for rep in range(2):
    order=[BASE,CAND] if pair%2==0 else [CAND,BASE];out.extend((a,off,delay,True) for a in order);pair+=1
 return out
def control_plan():return [(CAND,o,10,False) for o in OFFSETS]
def run_plan(root,plan,outfile,off):
 xv=start_xvfb(root);rows=[]
 try:
  for i,a in enumerate(plan):rows.append(run_case(root,off+i,*a))
 finally:xv.terminate();xv.wait(timeout=1)
 Path(outfile).write_text(json.dumps({'rows':rows},indent=2,sort_keys=True));return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['construction','formal-positive','formal-controls']);p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--batch',type=int,choices=range(4));a=p.parse_args();root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
 if a.mode=='construction':r=run_plan(root,construction_plan(),a.out,0);print(json.dumps(summarize(r[:4],r[4:]),indent=2,sort_keys=True))
 elif a.mode=='formal-positive':full=positive_plan();off=a.batch*8;r=run_plan(root,full[off:off+8],a.out,off);print(len(r))
 else:r=run_plan(root,control_plan(),a.out,32);print(len(r))
if __name__=='__main__':main()
