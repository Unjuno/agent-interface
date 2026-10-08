import sys,json,traceback
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from integrated_efficiency_client_v2 import RuntimeClient
c=RuntimeClient(Path('/out/client'),991064,chromium='/usr/bin/chromium');r={}
try:
 c.start();task=c.ready['goal']['tasks'][3];o=c.navigate(task);r={'status':'OBSERVED','task':task,'observation':o,'programs':c.programs,'durable_calls':c.durable_calls}
except Exception as e:r={'status':'FAILED','error':str(e)};traceback.print_exc()
finally:
 try:c.close()
 except Exception as e:r['cleanup_error']=str(e)
 Path('/out/result.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k not in ('programs','observation')}))
raise SystemExit(0 if r['status']=='OBSERVED' else 1)
