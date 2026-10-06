import sys,json,time,traceback
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from portable_client import RuntimeClient
from compiled_execution import CompiledExecution
result={};client=RuntimeClient(Path('/out/client'),991058)
try:
 client.start();task=client.ready['goal']['tasks'][0];source=client.navigate(task)
 aliases,failure=client.mint(task['layout'],source,{'field_point':[285,400],'submit_point':[376,400]},'graph_adapter')
 if failure: raise RuntimeError('target mint refused: '+json.dumps(failure))
 execution=CompiledExecution(client,task,aliases);result=execution.run()
 result['goal']=task;result['programs']=client.programs;result['durable_calls']=client.durable_calls
 result['independent_evaluation']=client.finish('finish-graph-adapter-991058')
 result['status']='GRAPH_OBSERVED'
except Exception as exc:
 result['status']='FAILED';result['error']={'type':type(exc).__name__,'detail':str(exc)};traceback.print_exc()
finally:
 try: client.close()
 except Exception as exc:result['cleanup_error']=str(exc)
 Path('/out/result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'status':result['status'],'receipt':result.get('receipt'),'error':result.get('error')}))
raise SystemExit(0 if result.get('receipt',{}).get('outcome')=='TASK_SUCCEEDED' and 'cleanup_error' not in result else 1)
