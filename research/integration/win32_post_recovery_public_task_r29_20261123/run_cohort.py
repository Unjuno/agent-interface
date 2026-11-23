from __future__ import annotations
import asyncio, base64, ctypes, hashlib, json, os, subprocess, sys, time, traceback
from datetime import timedelta
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

ROOT=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent
COND=json.loads((PACKET/'conditions.json').read_text(encoding='utf-8-sig'))
RAW=PACKET/'raw'
RAW.mkdir(exist_ok=True)
FENCE=Path(os.environ['LOCALAPPDATA'])/'Unjuno/AgentInterface/custody-v1/daad63552416ce22de89c5e5ff25be5951a6ee1973e4f1abf3533da1bf2fb445.json'
SCORER_PATH=PACKET/'source/scorer.py'
FIXTURE_PATH=PACKET/'source/fixture_app.py'
FG_PATH=PACKET/'source/foreground_probe.py'

def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def body(response):
 blocks=getattr(response,'content',None) or []
 texts=[getattr(b,'text',None) for b in blocks if getattr(b,'type',None)=='text' and isinstance(getattr(b,'text',None),str)]
 if len(texts)!=1: raise ValueError('expected one public text receipt')
 return json.loads(texts[0])
def raw_response(response):
 value=response.model_dump(mode='json') if hasattr(response,'model_dump') else str(response)
 return value
def report_from_review(value):
 return value.get('receipt',{}).get('source',{}).get('raw_report',{})
def producer_absent(identity):
 if type(identity) is not dict or type(identity.get('pid')) is not int or type(identity.get('creation_time_100ns')) is not int: return False,{'error':'producer_identity_invalid'}
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]; k.OpenProcess.restype=ctypes.c_void_p
 k.GetProcessTimes.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]; k.GetProcessTimes.restype=ctypes.c_int
 k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]; k.WaitForSingleObject.restype=ctypes.c_uint32
 k.CloseHandle.argtypes=[ctypes.c_void_p]; k.CloseHandle.restype=ctypes.c_int
 h=k.OpenProcess(0x00100000|0x1000,False,identity['pid'])
 if not h:
  err=ctypes.get_last_error()
  return (True,{'pid':identity['pid'],'open_error':err,'absent':True}) if err==87 else (False,{'pid':identity['pid'],'open_error':err,'absent':False})
 try:
  class FT(ctypes.Structure): _fields_=[('lo',ctypes.c_uint32),('hi',ctypes.c_uint32)]
  c,e,kt,ut=FT(),FT(),FT(),FT()
  if not k.GetProcessTimes(h,ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut)):
   return False,{'pid':identity['pid'],'creation_read_error':ctypes.get_last_error()}
  created=(int(c.hi)<<32)|int(c.lo)
  if created!=identity['creation_time_100ns']:
   return True,{'pid':identity['pid'],'recorded_creation_time_100ns':identity['creation_time_100ns'],'current_creation_time_100ns':created,'pid_reused_source_absent':True}
  wait=k.WaitForSingleObject(h,0)
  return (wait==0,{'pid':identity['pid'],'creation_time_100ns':created,'wait_status':wait,'absent':wait==0})
 finally: k.CloseHandle(h)

def close_fixture(hwnd,proc,folder):
 u=ctypes.WinDLL('user32',use_last_error=True)
 u.IsWindow.argtypes=[ctypes.c_void_p];u.IsWindow.restype=ctypes.c_int
 u.PostMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t];u.PostMessageW.restype=ctypes.c_int
 before=bool(u.IsWindow(ctypes.c_void_p(hwnd))); posted=bool(u.PostMessageW(ctypes.c_void_p(hwnd),0x0010,0,0)) if before else False
 try: proc.wait(timeout=5)
 except subprocess.TimeoutExpired: pass
 after=bool(u.IsWindow(ctypes.c_void_p(hwnd)))
 dump(folder/'fixture-cleanup.json',{'hwnd':hwnd,'window_before':before,'wm_close_posted':posted,'window_after':after,'process_pid':proc.pid,'process_exit_code':proc.poll()})
 return posted and not after and proc.poll() is not None

async def run_trial(cfg):
 folder=RAW/f'trial-{cfg["ordinal"]:02d}'; folder.mkdir()
 if not FENCE.exists(): raise RuntimeError('R24 native custody fence path missing')
 initial_fence=json.loads(FENCE.read_text(encoding='utf-8'))
 if initial_fence.get('status')!='clear' or initial_fence.get('pending') is not None: raise RuntimeError('persistent fence is not clear before trial')
 dump(folder/'fence-before.json',initial_fence)
 app= subprocess.Popen([sys.executable,str(FIXTURE_PATH),'--meta',str(folder/'fixture-meta.json'),'--effect',str(folder/'effect.json'),'--events',str(folder/'events.jsonl'),'--effect-delay-ms',str(cfg['effect_delay_ms']),'--state',str(folder/'fixture-state.json')],cwd=str(PACKET),stdout=(folder/'fixture.stdout.txt').open('wb'),stderr=(folder/'fixture.stderr.txt').open('wb'))
 deadline=time.monotonic()+10
 while time.monotonic()<deadline and not (folder/'fixture-meta.json').exists() and app.poll() is None: await asyncio.sleep(.05)
 if not (folder/'fixture-meta.json').exists(): raise RuntimeError('fixture did not become ready')
 meta=json.loads((folder/'fixture-meta.json').read_text()); hwnd=int(meta['hwnd']);
 targets=folder/'targets.json'; dump(targets,{'fixture':hwnd})
 window={'hwnd':hwnd,'pid':app.pid,'title':'Agent Interface Win32 Fixture R29','region':cfg['capture_region']};dump(folder/'window.json',window)
 activation_marker=folder/'computer-use-foreground-confirmed.json'
 activation_deadline=time.monotonic()+120
 while time.monotonic()<activation_deadline and not activation_marker.exists(): await asyncio.sleep(.1)
 if not activation_marker.exists(): raise RuntimeError('Computer Use exact-window activation marker missing; stopped before observation/dispatch')
 fg=subprocess.run([sys.executable,str(FG_PATH),str(hwnd),str(app.pid),str(folder/'foreground-pre-dispatch.json')],cwd=str(PACKET),capture_output=True,text=True)
 if fg.returncode: raise RuntimeError('exact fixture foreground preflight failed')
 server_args=['-m','runtime.cli_v1.mcp_server','--targets',str(targets),'--output-directory',str(folder/'source-mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms',str(cfg['horizon_ms'])]
 timeline=[]; callrows={}; source_public=None; close_ok=False
 async def source_session():
  nonlocal source_public,close_ok
  params=StdioServerParameters(command=sys.executable,args=server_args,cwd=str(ROOT))
  async with stdio_client(params) as (rd,wr):
   async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=40)) as s:
    await s.initialize()
    async def call(name,args):
     st=time.monotonic_ns(); resp=await s.call_tool(name,args); en=time.monotonic_ns(); cid=(cfg.get('calls') or {}).get(name+str(len(callrows)),None) or __import__('uuid').uuid4().hex
     model=raw_response(resp); dump(folder/'source-responses'/f'{name}-{cid}.json',model)
     callrows[cid]={'method':name,'args':args,'started_ns':st,'ended_ns':en,'response':model}; timeline.append({'session':'source','tool':name,'call_id':cid,'started_ns':st,'ended_ns':en})
     return body(resp),model
    obs,obs_raw=await call('interface_observe',{'target':'fixture','frame':cfg['capture_frame'],'region':cfg['capture_region']})
    rep=report_from_review(obs)
    if rep.get('status')!='returned' or rep.get('input_dispatched') is not False or rep.get('side_effect_authority') is not False: raise RuntimeError('pre-action observe did not prove no authority/no input')
    gen=rep.get('target_generation')
    if not isinstance(gen,str) or len(gen)!=64: raise RuntimeError('observation lacks target generation')
    image_blocks=[x for x in obs_raw.get('content',[]) if x.get('type')=='image' and x.get('mimeType')=='image/png']
    if len(image_blocks)!=1: raise RuntimeError('public observation PNG missing')
    (folder/'observe-before.png').write_bytes(base64.b64decode(image_blocks[0]['data'],validate=True))
    now=time.monotonic_ns(); program={'schema':'agent-interface/program-v1','program_id':cfg['program_id'],'source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen}},'authority':{'lease_id':cfg['lease_id'],'expires_at_ns':now+cfg['authority_lease_ms']*1_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
    dump(folder/'program.json',program)
    dispatched,dispatch_raw=await call('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000})
    action_id=dispatched.get('call_id')
    if not isinstance(action_id,str): raise RuntimeError('dispatch did not return exact call id')
    result,results_raw=await call('interface_results',{'call_id':action_id,'include_image':False})
    if result.get('action',{}).get('operation_id') is None: raise RuntimeError('exact results lookup omitted action')
    source_public=result
    after_obs,after_raw=await call('interface_observe',{'target':'fixture','frame':cfg['capture_frame'],'region':cfg['capture_region']})
    after_report=report_from_review(after_obs)
    if after_report.get('input_dispatched') is not False or after_report.get('side_effect_authority') is not False: raise RuntimeError('post-action observe failed no-input/no-authority proof')
    after_images=[x for x in after_raw.get('content',[]) if x.get('type')=='image' and x.get('mimeType')=='image/png']
    if len(after_images)==1: (folder/'observe-after.png').write_bytes(base64.b64decode(after_images[0]['data'],validate=True))
    closed,close_raw=await call('interface_close',{})
    close_ok=closed.get('status')=='closed'
    dump(folder/'source-session-close.json',closed)
  return action_id,gen,program,source_public,callrows,timeline

 try:
  action_id,source_gen,program,source_public,callrows,timeline=await source_session()
  action=source_public['action']; cancel=source_public.get('cancellation',{}).get('result',{})
  effect_deadline=time.monotonic()+10; effect=None
  while time.monotonic()<effect_deadline:
   try: effect=json.loads((folder/'effect.json').read_text(encoding='utf-8'))
   except (FileNotFoundError,json.JSONDecodeError): effect=None
   if effect and effect.get('verified') is True: break
   await asyncio.sleep(.05)
  spec=spec_from_file_location(f'r29_scorer_{cfg["ordinal"]}',PACKET/'source/scorer.py'); scorer=module_from_spec(spec);spec.loader.exec_module(scorer)
  success,state_bytes,score= scorer.score(folder/'events.jsonl',folder/'effect.json')
  dump(folder/'independent-score.json',{'scorer_id':'fixture-delayed-a-independent-v1','scorer_sha256':hashlib.sha256(SCORER_PATH.read_bytes()).hexdigest(),'task_success':success,'state_sha256':hashlib.sha256(state_bytes).hexdigest(),'effect':score})
  source_proof={'action_call_id':action_id,'operation_id':action.get('operation_id'),'target_generation':action.get('target_generation'),'status':action.get('status'),'input_dispatched':action.get('input_dispatched'),'release_confirmed':action.get('release_confirmed'),'task_success':action.get('task_success'),'replay_allowed':action.get('replay_allowed'),'cancellation':cancel}
  dump(folder/'source-action-summary.json',source_proof)
  trial={'ordinal':cfg['ordinal'],'trial_id':cfg['trial_id'],'target':window,'source':source_proof,'effect':effect,'score':{'task_success':success,'state_sha256':hashlib.sha256(state_bytes).hexdigest()},'source_calls':timeline,'outcome':'ACTION_TERMINAL','source_release_confirmed':action.get('release_confirmed') is True,'recovery_attempted':False,'recovery_release_confirmed':None,'recovery_horizon_verified':None,'fixture_closed':False}
  if action.get('status')=='unknown' and action.get('release_confirmed') is not True:
   identity=cancel.get('producer_identity'); absent,identity_check=producer_absent(identity)
   dump(folder/'producer-identity-check.json',identity_check)
   if not absent: trial['outcome']='STOP_PRODUCER_ABSENCE_UNCONFIRMED'; return trial
   obligations=cancel.get('obligations')
   if (not isinstance(identity,dict) or not isinstance(obligations,list) or not obligations or cancel.get('late_input_horizon_ns') not in (0,None)):
    trial['outcome']='STOP_SOURCE_CUSTODY_FIELDS_INVALID'; return trial
   custody={'classification':'UNKNOWN_RELEASE_UNCONFIRMED_STOPPED','operation_id':action['operation_id'],'target_generation':action['target_generation'],'obligations':obligations,'do_not_replay':True,'observed_producer_live':False,'late_server_request_possible':True,'dispatch':{'input_dispatched':True,'release_confirmed':False,'task_success':None,'replay_allowed':False}}
   dump(folder/'source-custody-record.json',custody)
   rec_args=['-m','runtime.cli_v1.mcp_server','--targets',str(targets),'--output-directory',str(folder/'recovery-mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms',str(cfg['horizon_ms'])]
   params=StdioServerParameters(command=sys.executable,args=rec_args,cwd=str(ROOT))
   async with stdio_client(params) as (rd,wr):
    async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=40)) as s:
     await s.initialize()
     t0=time.monotonic_ns(); ob=await s.call_tool('interface_observe',{'target':'fixture','frame':cfg['capture_frame'],'region':cfg['capture_region']});t1=time.monotonic_ns(); obbody=body(ob);obreport=report_from_review(obbody);timeline.append({'session':'recovery','tool':'interface_observe','started_ns':t0,'ended_ns':t1,'status':obreport.get('status'),'observation_id':obreport.get('observation_id'),'target_generation':obreport.get('target_generation'),'input_dispatched':obreport.get('input_dispatched'),'side_effect_authority':obreport.get('side_effect_authority')});dump(folder/'recovery-observation-response.json',raw_response(ob))
     if obreport.get('status')!='returned' or obreport.get('input_dispatched') is not False or obreport.get('side_effect_authority') is not False: trial['outcome']='STOP_RECOVERY_OBSERVATION_INVALID'; return trial
     recovery_gen=obreport.get('target_generation');
     fg2=subprocess.run([sys.executable,str(FG_PATH),str(hwnd),str(app.pid),str(folder/'foreground-pre-recovery.json')],cwd=str(PACKET),capture_output=True,text=True);dump(folder/'foreground-recovery-probe.json',{'returncode':fg2.returncode,'stdout':fg2.stdout,'stderr':fg2.stderr})
     if fg2.returncode: trial['outcome']='STOP_RECOVERY_TARGET_FOREGROUND_MISMATCH'; return trial
     trial['recovery_attempted']=True
     t0=time.monotonic_ns(); recresp=await s.call_tool('interface_recover_orphaned_input',{'source_operation_id':action['operation_id'],'source_target_generation':action['target_generation'],'recovery_target_generation':recovery_gen,'obligations':obligations,'source_custody_record':custody});t1=time.monotonic_ns(); recbody=body(recresp);timeline.append({'session':'recovery','tool':'interface_recover_orphaned_input','started_ns':t0,'ended_ns':t1,'status':recbody.get('status'),'call_id':recbody.get('call_id'),'release_confirmed':recbody.get('release_confirmed')});dump(folder/'orphan-recovery-public-response.json',raw_response(recresp));dump(folder/'orphan-recovery-body.json',recbody)
     final=recbody
     rid=recbody.get('call_id')
     if recbody.get('status')=='pending' and isinstance(rid,str):
      deadline=time.monotonic()+35
      while time.monotonic()<deadline:
       await asyncio.sleep(.2); q0=time.monotonic_ns(); q=await s.call_tool('interface_results',{'call_id':rid,'include_image':False,'compact':True,'detail':'brief'});q1=time.monotonic_ns(); final=body(q);timeline.append({'session':'recovery','tool':'interface_results','started_ns':q0,'ended_ns':q1,'status':final.get('status'),'release_confirmed':final.get('release_confirmed')});dump(folder/f'recovery-results-{uuid.uuid4().hex}.json',raw_response(q))
       if final.get('status')!='pending': break
     trial['recovery_status']=final.get('status');trial['recovery_release_confirmed']=final.get('release_confirmed') is True
     rr=final.get('recovery_receipt',{});trial['recovery_horizon_verified']=rr.get('late_input_horizon_verified') is True
     trial['recovery_receipt_summary']={'source_action_status':final.get('source_action_status'),'source_operation_id':final.get('source_operation_id'),'source_target_generation':final.get('source_target_generation'),'recovery_target_generation':final.get('recovery_target_generation'),'release_confirmed':final.get('release_confirmed'),'task_success':final.get('task_success'),'replay_allowed':final.get('replay_allowed'),'late_input_horizon_ns':rr.get('late_input_horizon_ns'),'late_input_horizon_verified':rr.get('late_input_horizon_verified'),'late_input_observation_count':rr.get('late_input_observation_count'),'late_input_max_observed_gap_ns':rr.get('late_input_max_observed_gap_ns'),'late_input_max_sample_gap_ns':rr.get('late_input_max_sample_gap_ns'),'readback_neutral':rr.get('readback',{}).get('neutral')}
     trial['outcome']='RECOVERY_VERIFIED' if trial['recovery_release_confirmed'] and trial['recovery_horizon_verified'] and trial['recovery_receipt_summary']['readback_neutral'] is True and final.get('source_action_status')=='unknown' and final.get('replay_allowed') is False else 'STOP_RECOVERY_UNVERIFIED'
     if trial['outcome']!='RECOVERY_VERIFIED': return trial
     t0=time.monotonic_ns(); closed_resp=await s.call_tool('interface_close',{});t1=time.monotonic_ns(); closed_body=body(closed_resp); timeline.append({'session':'recovery','tool':'interface_close','started_ns':t0,'ended_ns':t1,'status':closed_body.get('status')});dump(folder/'recovery-session-close.json',closed_body)
  if trial['outcome']=='RECOVERY_VERIFIED':
   # A recovered generation cannot be reused. Require a new Computer Use
   # activation and foreground proof, then a fresh public observation/action.
   marker=folder/'computer-use-followup-foreground-confirmed.json'
   deadline=time.monotonic()+120
   while time.monotonic()<deadline and not marker.exists(): await asyncio.sleep(.1)
   if not marker.exists(): trial['outcome']='STOP_FOLLOWUP_ACTIVATION_MISSING'
   else:
    fg3=subprocess.run([sys.executable,str(FG_PATH),str(hwnd),str(app.pid),str(folder/'foreground-pre-followup.json')],cwd=str(PACKET),capture_output=True,text=True)
    dump(folder/'foreground-followup-probe.json',{'returncode':fg3.returncode,'stdout':fg3.stdout,'stderr':fg3.stderr})
    if fg3.returncode: trial['outcome']='STOP_FOLLOWUP_FOREGROUND_MISMATCH'
    else:
     effect_deadline=time.monotonic()+12; old_effect=None
     while time.monotonic()<effect_deadline:
      try: old_effect=json.loads((folder/'effect.json').read_text(encoding='utf-8-sig'))
      except (FileNotFoundError,json.JSONDecodeError): old_effect=None
      if old_effect and old_effect.get('verified') is True: break
      await asyncio.sleep(.05)
     dump(folder/'pre-followup-state.json',json.loads((folder/'fixture-state.json').read_text(encoding='utf-8-sig')) if (folder/'fixture-state.json').exists() else {'missing':True})
     if not old_effect or old_effect.get('verified') is not True or json.loads((folder/'fixture-state.json').read_text(encoding='utf-8-sig')).get('text')!='a': trial['outcome']='STOP_PRIOR_EFFECT_NOT_OBSERVED'
     else:
      args3=[sys.executable,str(PACKET/'task_oracle_server.py'),str(targets),str(folder/'task-mcp'),str(folder/'fixture-state.json'),str(folder/'events.jsonl')]
      params=StdioServerParameters(command=sys.executable,args=args3,cwd=str(ROOT))
      async with stdio_client(params) as (rd3,wr3):
       async with ClientSession(rd3,wr3,read_timeout_seconds=timedelta(seconds=40)) as s3:
        await s3.initialize()
        async def call3(name,args):
         q0=time.monotonic_ns(); q=await s3.call_tool(name,args); q1=time.monotonic_ns(); dump(folder/f'task-{name}-{uuid.uuid4().hex}.json',raw_response(q)); timeline.append({'session':'followup','tool':name,'started_ns':q0,'ended_ns':q1}); return body(q)
        o3=await call3('interface_observe',{'target':'fixture','frame':cfg['capture_frame'],'region':cfg['capture_region']})
        rep3=report_from_review(o3); gen3=rep3.get('target_generation')
        if rep3.get('status')!='returned' or rep3.get('input_dispatched') is not False or rep3.get('side_effect_authority') is not False or not isinstance(gen3,str): trial['outcome']='STOP_FOLLOWUP_OBSERVE_INVALID'
        else:
         now3=time.monotonic_ns(); pid3=cfg['followup_program_id']; lease3=cfg['followup_lease_id']
         prog3={'schema':'agent-interface/program-v1','program_id':pid3,'source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen3}},'authority':{'lease_id':lease3,'expires_at_ns':now3+60_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['B']},{'op':'release_all'}]}
         dump(folder/'followup-program.json',prog3)
         d3=await call3('interface_dispatch',{'program':prog3,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000}); cid3=d3.get('call_id')
         if not isinstance(cid3,str): trial['outcome']='STOP_FOLLOWUP_NO_CALL_ID'
         else:
          r3=await call3('interface_results',{'call_id':cid3,'include_image':False})
          end3=time.monotonic()+25
          while r3.get('action',{}).get('status')=='pending' and time.monotonic()<end3:
           await asyncio.sleep(.25); r3=await call3('interface_results',{'call_id':cid3,'include_image':False})
          dump(folder/'followup-action-result.json',r3)
          if r3.get('action',{}).get('status')!='completed' or r3.get('action',{}).get('release_confirmed') is not True: trial['outcome']='STOP_FOLLOWUP_ACTION_NOT_RELEASED'
          else:
           v3=await call3('interface_verify_task',{'call_id':cid3,'wait_for_result_ms':5000}); dump(folder/'followup-task-verification.json',v3)
           trial['followup_call_id']=cid3; trial['followup_operation_id']=r3['action'].get('operation_id'); trial['followup_task_success']=v3.get('task_success')
           trial['followup_status']=r3.get('action',{}).get('status'); trial['followup_release_confirmed']=r3.get('action',{}).get('release_confirmed')
           trial['outcome']='RECOVERY_AND_NEW_TASK_VERIFIED' if v3.get('status')=='verified' and v3.get('task_success') is True and v3.get('replay_allowed') is False else 'STOP_FOLLOWUP_TASK_UNVERIFIED'
          c3=await call3('interface_close',{}); dump(folder/'followup-session-close.json',c3)
      trial['fixture_closed']=close_fixture(hwnd,app,folder) if trial['outcome']=='RECOVERY_AND_NEW_TASK_VERIFIED' else False

  final_fence=json.loads(FENCE.read_text(encoding='utf-8'));dump(folder/'fence-after.json',final_fence)
  trial['fence_status_after']=final_fence.get('status');trial['fence_last_resolved']=final_fence.get('last_resolved');trial['fixture_closed']=trial['fixture_closed'] or (not ctypes.windll.user32.IsWindow(ctypes.c_void_p(hwnd)))
  if not (final_fence.get('status')=='clear' and final_fence.get('pending') is None and final_fence.get('last_resolved',{}).get('operation_id')==(trial.get('followup_operation_id') or action.get('operation_id'))): trial['outcome']='STOP_DURABLE_FENCE_NOT_CLEAR'
  if not trial['fixture_closed']: trial['outcome']='STOP_FIXTURE_CLOSE_UNVERIFIED'
  return trial
 except BaseException as exc:
  dump(folder/'trial-exception.json',{'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
  try:
   if 'hwnd' in locals() and 'app' in locals() and source_public and source_public.get('action',{}).get('release_confirmed') is True: close_fixture(hwnd,app,folder)
  except Exception: pass
  raise

async def main():
 progress_path=RAW/'cohort-progress.json'
 if not progress_path.exists(): raise SystemExit('R27 empty progress ledger missing; refusing to run')
 progress=json.loads(progress_path.read_text(encoding='utf-8-sig'))
 if progress.get('completed_trials')!=0 or progress.get('trials'): raise SystemExit('R29 is frozen once; existing progress means refusing a repeat')
 summaries=[]
 for cfg in COND['trials']:
  summary=await run_trial(cfg); summaries.append(summary);dump(RAW/'cohort-progress.json',{'schema':'agent-interface/r27-progress-v1','completed_trials':len(summaries),'trials':summaries})
  if not summary.get('fixture_closed') or summary.get('outcome') not in ('RECOVERY_AND_NEW_TASK_VERIFIED',):
   break
  print(json.dumps({'ordinal':summary['ordinal'],'outcome':summary['outcome'],'action_status':summary['source']['status'],'source_release_confirmed':summary['source']['release_confirmed'],'recovery_release_confirmed':summary.get('recovery_release_confirmed'),'horizon_verified':summary.get('recovery_horizon_verified'),'score':summary['score']['task_success'],'fixture_closed':summary['fixture_closed']}),flush=True)
 dump(RAW/'cohort-summary.json',{'schema':'agent-interface/r27-summary-v1','source_main':COND['source_main'],'frozen_trials':len(COND['trials']),'attempts':summaries,'stopped_early':len(summaries)<len(COND['trials']),'cohort_outcome':'PASS_SCOPED_SINGLE_ATTEMPT_POST_RECOVERY_TASK' if len(summaries)==len(COND['trials']) and all(x['outcome']=='RECOVERY_AND_NEW_TASK_VERIFIED' for x in summaries) else 'FAIL_OR_MIXED_OR_STOPPED'})
 print(json.dumps({'cohort_trials':len(summaries),'outcome':'PASS_SCOPED_SINGLE_ATTEMPT_POST_RECOVERY_TASK' if len(summaries)==len(COND['trials']) and all(x['outcome']=='RECOVERY_AND_NEW_TASK_VERIFIED' for x in summaries) else 'FAIL_OR_MIXED_OR_STOPPED'},indent=2),flush=True)
asyncio.run(main())
