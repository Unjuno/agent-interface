import json,sys,time
from pathlib import Path
from policy import classify,coarse
root=Path(__file__).resolve().parent
if len(sys.argv)!=2: raise SystemExit('usage: runner.py OUTPUT')
out=Path(sys.argv[1]); out.parent.mkdir(parents=True,exist_ok=True)
rows=json.loads((root/'corpus.json').read_text())
started=time.monotonic_ns(); result=[]
for e in rows:
    result.append({'row_id':e['row_id'],'evidence':e,'candidate':classify(e),'comparator':coarse(e)})
payload={'allocation':'typed-negative-outcome-4174-20260923-01','started_ns':started,'ended_ns':time.monotonic_ns(),
         'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'rows':result}
out.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
print(json.dumps({'rows':len(result),'output':str(out)}))
