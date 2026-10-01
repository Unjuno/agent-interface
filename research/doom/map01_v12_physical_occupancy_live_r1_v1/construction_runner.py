import argparse,json,traceback
from pathlib import Path
from run_session import run_one
from evaluate import evaluate
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--v12',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
try:
 runtime=run_one(a.source,a.v12,a.out/'session1',192801,'r1-construction'); result=evaluate(runtime,'r1-construction'); result['construction_invocations']=1;result['reruns']=0
 (a.out/'CONSTRUCTION_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['pass'] else 1)
except SystemExit:raise
except BaseException as exc:
 stop={'decision':'FAIL_CONSTRUCTION_RUNTIME_OR_SCHEMA','construction_invocations':1,'reruns':0,'error':repr(exc),'traceback':traceback.format_exc()};(a.out/'CONSTRUCTION_STOP.json').write_text(json.dumps(stop,indent=2,sort_keys=True)+'\n');print(json.dumps(stop,sort_keys=True));raise SystemExit(1)
