"""Synthetic runtime with a real stdin/stdout split-clock gate; no GUI or inputs."""
import json,sys,time
from pathlib import Path
root=Path(sys.argv[1])
def emit(record):
 record['emitted_ns']=time.perf_counter_ns()
 with (root/'runtime-events.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 print(json.dumps(record),flush=True)
emit({'event':'observation','id':'initial','sequence':1,'image':'synthetic-reference-only','scope':'no image capture'})
emit({'event':'command','command':{'op':'clock','transport_request_id':'old-clock'}})
emit({'event':'clock','runtime_ns':1,'sequence':1})
for line in sys.stdin:
 command=json.loads(line);emit({'event':'command','command':command})
 if command['op']=='clock':
  deadline=time.monotonic()+30
  while not (root/'release-clock').exists():
   if time.monotonic()>deadline:raise TimeoutError('test gate not released')
   time.sleep(.005)
  emit({'event':'clock','runtime_ns':time.perf_counter_ns(),'sequence':1})
 elif command['op']=='finish':
  emit({'event':'independent_evaluation','scope':'fixture shutdown only','task_success':None});break
 else:raise ValueError('fixture accepts clock/finish only')
