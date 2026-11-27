import asyncio,json,sys,time
from datetime import timedelta,datetime,timezone
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();args=['-m','runtime.cli_v1.mcp_server','--targets',str(out/'targets.json'),'--output-directory',str(out/'mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms','2000']
def raw(x):return x.model_dump(mode='json',exclude_none=True)
def texts(x):return [b.text for b in x.content if getattr(b,'type',None)=='text']
def obj(x):
 ts=texts(x)
 for t in ts:
  try:return json.loads(t)
  except Exception:pass
 return {'texts':ts,'isError':x.isError}
def save(name,x): (out/name).write_text(json.dumps(raw(x),indent=2),encoding='utf-8')
async def main():
 params=StdioServerParameters(command=sys.executable,args=args,cwd=str(repo))
 timeline=[]
 async with stdio_client(params) as (read,write):
  async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=45)) as s:
   await s.initialize()
   ob=await s.call_tool('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':[80,80,420,220]});save('observation.json',ob)
   o=obj(ob);r=(o.get('receipt',{}).get('source',{}).get('raw_report') if isinstance(o,dict) else None)
   if not isinstance(r,dict) or r.get('status')!='returned' or r.get('target_generation_consistency')!='matched':
    (out/'stop.json').write_text(json.dumps({'reason':'observation preflight refused','observation':o},indent=2),encoding='utf-8');return
   now=time.monotonic_ns();gen=r['target_generation']
   program={'schema':'agent-interface/program-v1','program_id':'win32-live-fixture-r02','source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen}},'authority':{'lease_id':'win32-live-fixture-r02','expires_at_ns':now+30_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
   before=(out/'events.jsonl').read_text(encoding='utf-8').splitlines() if (out/'events.jsonl').exists() else []
   start={'utc':datetime.now(timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns(),'target_generation':gen,'events_before':before};(out/'dispatch-start.json').write_text(json.dumps(start,indent=2),encoding='utf-8')
   d=await s.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000});save('dispatch.json',d);v=obj(d);timeline.append({'time_utc':datetime.now(timezone.utc).isoformat(),'operation':'dispatch','response':v})
   callid=v.get('call_id') if isinstance(v,dict) else None
   if v.get('status')=='pending' and callid:
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
     await asyncio.sleep(.25)
     res=await s.call_tool('interface_results',{'call_id':callid,'include_image':False});rv=obj(res);timeline.append({'time_utc':datetime.now(timezone.utc).isoformat(),'operation':'results','response':rv})
     if rv.get('status')!='pending':break
    else:
     cancel=await s.call_tool('interface_cancel',{'call_id':callid});cv=obj(cancel);timeline.append({'time_utc':datetime.now(timezone.utc).isoformat(),'operation':'cancel_at_25s_bound','response':cv})
     for _ in range(80):
      await asyncio.sleep(.25);res=await s.call_tool('interface_results',{'call_id':callid,'include_image':False});rv=obj(res);timeline.append({'time_utc':datetime.now(timezone.utc).isoformat(),'operation':'results_after_cancel','response':rv})
      if rv.get('status')!='pending':break
   (out/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
   (out/'terminal.json').write_text(json.dumps(v if v.get('status')!='pending' else rv,indent=2),encoding='utf-8')
   events=(out/'events.jsonl').read_text(encoding='utf-8').splitlines() if (out/'events.jsonl').exists() else []
   (out/'events-final.json').write_text(json.dumps([json.loads(x) for x in events],indent=2),encoding='utf-8')
   close=await s.call_tool('interface_close',{});save('close.json',close)
   (out/'summary.json').write_text(json.dumps({'initial_dispatch_status':v.get('status'),'call_id':callid,'terminal_status':(v if v.get('status')!='pending' else rv).get('status'),'timeline_rows':len(timeline),'events_before':before,'events_final':[json.loads(x) for x in events],'close':obj(close)},indent=2),encoding='utf-8')
   print((out/'summary.json').read_text(encoding='utf-8'))
asyncio.run(main())
