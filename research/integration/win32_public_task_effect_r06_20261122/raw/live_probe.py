import asyncio, json, sys, time, hashlib
from datetime import timedelta, datetime, timezone
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); cfg=json.loads((out/'raw/window.json').read_text(encoding='utf-8-sig')); x1,y1,x2,y2=cfg['rect']; region=[x1,y1,x2-x1,y2-y1]
args=['-m','runtime.cli_v1.mcp_server','--targets',str(out/'raw/targets.json'),'--output-directory',str(out/'raw/mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms','2000']
def save(name,x): (out/'raw'/name).write_text(json.dumps(x.model_dump(mode='json',exclude_none=True),indent=2),encoding='utf-8')
def body(x):
 for b in x.content:
  if getattr(b,'type',None)=='text':
   try:return json.loads(b.text)
   except Exception:pass
 return {'isError':x.isError,'content':[{'type':getattr(b,'type',None),'text':getattr(b,'text',None)} for b in x.content]}
def is_terminal(x):
 if not isinstance(x,dict): return False
 a=x.get('action') or {}
 return a.get('status') in ('completed','recovered','unknown') or x.get('status') in ('returned','recovered','unknown','runtime_failed','receipt_unavailable')
async def main():
 params=StdioServerParameters(command=sys.executable,args=args,cwd=str(repo)); timeline=[]
 async with stdio_client(params) as (rd,wr):
  async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=50)) as s:
   await s.initialize()
   before_ns=time.monotonic_ns(); ob=await s.call_tool('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':region}); save('observe-before.json',ob); pre=body(ob); br=pre.get('receipt',{}).get('source',{}).get('raw_report',{}); gen=br.get('target_generation')
   if pre.get('isError') or not isinstance(gen,str) or br.get('status')!='returned':
    (out/'raw/summary.json').write_text(json.dumps({'status':'STOP_NO_BEFORE_OBSERVATION','response':pre},indent=2)); return
   gcmd=__import__('subprocess').run([sys.executable,str(out/'source/foreground_probe.py'),str(cfg['hwnd']),str(cfg['pid']),str(out/'raw/foreground-pre-dispatch.json')],cwd=str(out),capture_output=True,text=True)
   fg=json.loads((out/'raw/foreground-pre-dispatch.json').read_text())
   if gcmd.returncode or not fg.get('foreground_matches'):
    (out/'raw/summary.json').write_text(json.dumps({'status':'STOP_FOREGROUND_MISMATCH','foreground':fg},indent=2)); return
   now=time.monotonic_ns(); uid=json.loads((out/'conditions.json').read_text())
   program={'schema':'agent-interface/program-v1','program_id':uid['program_id'],'source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen}},'authority':{'lease_id':uid['lease_id'],'expires_at_ns':now+60_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
   ds=time.monotonic_ns(); d=await s.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000}); save('dispatch.json',d); dv=body(d); callid=dv.get('call_id'); timeline.append({'tool':'interface_dispatch','started_ns':ds,'ended_ns':time.monotonic_ns(),'body':dv}); row=dv
   if not isinstance(callid,str):
    (out/'raw/summary.json').write_text(json.dumps({'status':'FAIL_NO_CALL_ID','dispatch':dv},indent=2)); return
   deadline=time.monotonic()+20
   while not is_terminal(row) and time.monotonic()<deadline:
    await asyncio.sleep(.2); st=time.monotonic_ns(); r=await s.call_tool('interface_results',{'call_id':callid,'include_image':False}); save('results-poll.json',r); row=body(r); timeline.append({'tool':'interface_results','started_ns':st,'ended_ns':time.monotonic_ns(),'body':row})
   # Exact terminal lookup is mandatory even when dispatch itself returned terminal.
   st=time.monotonic_ns(); rr=await s.call_tool('interface_results',{'call_id':callid,'include_image':False}); save('results-exact.json',rr); row=body(rr); timeline.append({'tool':'interface_results_exact','started_ns':st,'ended_ns':time.monotonic_ns(),'body':row})
   if not is_terminal(row):
    cs=time.monotonic_ns(); cr=await s.call_tool('interface_cancel',{'call_id':callid}); save('cancel-once.json',cr); timeline.append({'tool':'interface_cancel_once','started_ns':cs,'ended_ns':time.monotonic_ns(),'body':body(cr)})
    deadline=time.monotonic()+20
    while not is_terminal(row) and time.monotonic()<deadline:
     await asyncio.sleep(.2); r=await s.call_tool('interface_results',{'call_id':callid,'include_image':False}); row=body(r); timeline.append({'tool':'interface_results_after_cancel','ended_ns':time.monotonic_ns(),'body':row})
   terminal_ns=time.monotonic_ns(); (out/'raw/terminal.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
   deadline=time.monotonic()+10; effect=None
   while time.monotonic()<deadline:
    try: effect=json.loads((out/'raw/effect.json').read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError): effect=None
    if effect and effect.get('verified') is True: break
    await asyncio.sleep(.05)
   # After observation is deliberately after oracle effect and exact result lookup.
   after_start=time.monotonic_ns(); after=await s.call_tool('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':region}); after_end=time.monotonic_ns(); save('observe-after.json',after); post=body(after); ar=post.get('receipt',{}).get('source',{}).get('raw_report',{}); timeline.append({'tool':'interface_observe_after','started_ns':after_start,'ended_ns':after_end,'body':post})
   ev=[]
   ep=out/'raw/events.jsonl'
   if ep.exists(): ev=[json.loads(z) for z in ep.read_text(encoding='utf-8').splitlines() if z.strip()]
   before_state={'text':'','accepted':False}; after_state={'text':effect.get('text') if effect else None,'accepted':any(x.get('kind')=='key_down_accepted' for x in ev)}
   scoring={'schema':'agent-interface/task-effect-score-receipt-v1','run_id':uid['run_id'],'task_id':'r06-delayed-a-key-effect','action_call_id':callid,'action_operation_id':row.get('action',{}).get('operation_id') or dv.get('operation_id'),'target_generation':gen,'scorer_id':'independent-fixture-event-oracle-v1','task_success':bool(effect and effect.get('verified') is True and effect.get('text')=='a' and after_state['accepted']),'before_state':before_state,'after_state':after_state,'effect_interval_ns':{'lower_ns':effect.get('key_down_accepted_ns') if effect else None,'upper_ns':effect.get('effect_observed_ns') if effect else None},'before_observation':{'started_ns':before_ns,'generation':gen},'after_observation':{'started_ns':after_start,'ended_ns':after_end,'generation':ar.get('target_generation')}}
   (out/'raw/task-score.json').write_text(json.dumps(scoring,indent=2),encoding='utf-8'); (out/'raw/timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
   close={'status':'not_called_nonterminal'}
   if is_terminal(row):
    c=await s.call_tool('interface_close',{}); save('close.json',c); close=body(c)
   summary={'status':'PASS_SCOPED_FIXTURE_EFFECT' if scoring['task_success'] and row.get('action',{}).get('release_confirmed') is True else 'FAIL_OR_UNKNOWN','run_id':uid['run_id'],'target_generation':gen,'call_id':callid,'operation_id':scoring['action_operation_id'],'dispatch_status':dv.get('status'),'terminal_action_status':row.get('action',{}).get('status'),'release_confirmed':row.get('action',{}).get('release_confirmed'),'task_success_public':row.get('task_success'),'independent_task_success':scoring['task_success'],'effect':effect,'events':ev,'after_generation':ar.get('target_generation'),'close':close,'terminal_seen_ns':terminal_ns}
   (out/'raw/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2))
asyncio.run(main())
