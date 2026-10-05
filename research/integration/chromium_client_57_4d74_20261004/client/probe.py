import sys,json,traceback
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from integrated_efficiency_client_v1 import RuntimeClient
client=RuntimeClient(Path('/out/client'),991057)
result={}
try:
 client.start()
 task=client.ready['goal']['tasks'][0]
 observation=client.navigate(task)
 result={'status':'OBSERVED','task_id':task['task_id'],'source_sequence':observation['sequence'],'capture_ns':observation['capture_ns'],'image':observation['image'],'programs':client.programs,'durable_calls':client.durable_calls}
except Exception as exc:
 result={'status':'FAILED','error_type':type(exc).__name__,'detail':str(exc)}
 traceback.print_exc()
finally:
 try: client.close()
 except Exception as exc: result['cleanup_error']=str(exc)
 Path('/out/result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='programs'}))
raise SystemExit(0 if result['status']=='OBSERVED' and 'cleanup_error' not in result else 1)
