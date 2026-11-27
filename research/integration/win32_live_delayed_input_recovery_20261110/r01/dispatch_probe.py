import asyncio, json, sys, time
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

root=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
args=['-m','runtime.cli_v1.mcp_server','--targets',str(out/'targets.json'),
 '--output-directory',str(out/'mcp'),'--session-mode','supervised-win32',
 '--supervised-win32-late-input-horizon-ms','2000']
def raw(x): return x.model_dump(mode='json',exclude_none=True)
def texts(x): return [b.text for b in x.content if getattr(b,'type',None)=='text']
async def main():
 params=StdioServerParameters(command=sys.executable,args=args,cwd=str(root))
 async with stdio_client(params) as (read,write):
  async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as s:
   await s.initialize()
   obs=await s.call_tool('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':[87,80,406,213]})
   (out/'observation-dispatch.json').write_text(json.dumps(raw(obs),indent=2),encoding='utf-8')
   msg=json.loads(texts(obs)[0]); report=msg['receipt']['source']['raw_report']
   if report.get('status')!='returned' or report.get('target_generation_consistency')!='matched':
    raise RuntimeError('fresh native observation not accepted; stopped before input')
   now=time.monotonic_ns()
   program={'schema':'agent-interface/program-v1','program_id':'win32-live-fixture-r01',
    'source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':report['target_generation']}},
    'authority':{'lease_id':'win32-live-fixture-r01','expires_at_ns':now+10_000_000_000},
    'terminal':{'release_all_required':True},
    'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
   result=await s.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,
    'current_binding_revision':1,'wait_for_result_ms':5000})
   (out/'dispatch.json').write_text(json.dumps(raw(result),indent=2),encoding='utf-8')
   result_texts=texts(result)
   (out/'dispatch-summary.json').write_text(json.dumps({'text':result_texts,'isError':result.isError},indent=2),encoding='utf-8')
   time.sleep(3)
   events=(out/'events.jsonl').read_text(encoding='utf-8').splitlines()
   (out/'events-post-horizon.json').write_text(json.dumps([json.loads(x) for x in events],indent=2),encoding='utf-8')
   print(json.dumps({'dispatch_text':result_texts,'isError':result.isError,
    'events_after_3s':[json.loads(x) for x in events]},indent=2))
asyncio.run(main())
