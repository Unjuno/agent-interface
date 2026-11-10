import asyncio,json,sys,time
from datetime import timedelta,datetime,timezone
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();cfg=json.loads((out/'window.json').read_text(encoding='utf-8-sig'));x1,y1,x2,y2=cfg['rect'];region=[x1,y1,x2-x1,y2-y1]
args=['-m','runtime.cli_v1.mcp_server','--targets',str(out/'targets.json'),'--output-directory',str(out/'mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms','2000']
def raw(x):return x.model_dump(mode='json',exclude_none=True)
def texts(x):return [b.text for b in x.content if getattr(b,'type',None)=='text']
def obj(x):
 for t in texts(x):
  try:return json.loads(t)
  except Exception:pass
 return {'texts':texts(x),'isError':x.isError}
def save(name,x):(out/name).write_text(json.dumps(raw(x),indent=2),encoding='utf-8')
def terminal(row):
 if not isinstance(row,dict):return False
 if row.get('status')=='pending':return False
 action=row.get('action')
 if isinstance(action,dict):return action.get('status') in ('completed','recovered','unknown')
 return row.get('status') in ('returned','recovered','unknown','runtime_failed','receipt_unavailable')
async def main():
 params=StdioServerParameters(command=sys.executable,args=args,cwd=str(repo));timeline=[]
 async with stdio_client(params) as (reader,writer):
  async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=50)) as s:
   await s.initialize();ob=await s.call_tool('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':region});save('observation.json',ob);o=obj(ob);report=o.get('receipt',{}).get('source',{}).get('raw_report')
   if not isinstance(report,dict) or report.get('status')!='returned' or report.get('target_generation_consistency')!='matched':
    (out/'stop.json').write_text(json.dumps({'reason':'observation refused','response':o},indent=2),encoding='utf-8');return
   gen=report['target_generation'];now=time.monotonic_ns();program={'schema':'agent-interface/program-v1','program_id':'win32-live-fixture-r03','source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen}},'authority':{'lease_id':'win32-live-fixture-r03','expires_at_ns':now+60_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
   before=(out/'events.jsonl').read_text(encoding='utf-8').splitlines() if (out/'events.jsonl').exists() else [];start={'utc':datetime.now(timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns(),'generation':gen,'region':region,'events_before':before};(out/'dispatch-start.json').write_text(json.dumps(start,indent=2),encoding='utf-8')
   d=await s.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000});save('dispatch.json',d);dv=obj(d);timeline.append({'utc':datetime.now(timezone.utc).isoformat(),'operation':'dispatch','response':dv});callid=dv.get('call_id')
   row=dv;deadline=time.monotonic()+20
   while not terminal(row) and time.monotonic()<deadline:
    await asyncio.sleep(.25);res=await s.call_tool('interface_results',{'call_id':callid,'include_image':False});row=obj(res);timeline.append({'utc':datetime.now(timezone.utc).isoformat(),'operation':'results','action_status':row.get('action',{}).get('status'),'response':row})
   if not terminal(row):
    can=await s.call_tool('interface_cancel',{'call_id':callid});cv=obj(can);timeline.append({'utc':datetime.now(timezone.utc).isoformat(),'operation':'single_timeout_cancel','response':cv})
    deadline=time.monotonic()+20
    while not terminal(row) and time.monotonic()<deadline:
     await asyncio.sleep(.25);res=await s.call_tool('interface_results',{'call_id':callid,'include_image':False});row=obj(res);timeline.append({'utc':datetime.now(timezone.utc).isoformat(),'operation':'results_after_cancel','action_status':row.get('action',{}).get('status'),'response':row})
   (out/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8');(out/'terminal.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
   ev=[json.loads(x) for x in (out/'events.jsonl').read_text(encoding='utf-8').splitlines()] if (out/'events.jsonl').exists() else [];(out/'events-final.json').write_text(json.dumps(ev,indent=2),encoding='utf-8')
   if terminal(row):
    cl=await s.call_tool('interface_close',{});save('close.json',cl);close=obj(cl)
   else:close={'status':'not_called_pending'}
   summary={'initial_status':dv.get('status'),'call_id':callid,'terminal_action_status':row.get('action',{}).get('status'),'public_terminal_status':row.get('status'),'release_confirmed':row.get('action',{}).get('release_confirmed',row.get('release_confirmed')),'task_success':row.get('task_success'),'replay_allowed':row.get('replay_allowed'),'event_rows':ev,'timeline_count':len(timeline),'close':close};(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
asyncio.run(main())
