import json,sys
from pathlib import Path
from audit import audit
root=Path(__file__).resolve().parent
src,out=map(lambda x:Path(x).resolve(),sys.argv[1:3])
if out.exists(): raise SystemExit("STOP_OUTPUT_COLLISION")
fixture=json.loads((root/"fixture_public.json").read_text(encoding="utf-8"))
oracle=json.loads((root/"oracle_truth.json").read_text(encoding="utf-8"))
raw=json.loads(src.read_text(encoding="utf-8"))
result=audit(fixture,oracle,raw)
out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":result["status"],"rows":result["rows"],"errors":result["errors"],"output":str(out)}))
sys.exit(0 if result["status"]=="METHOD_PASS_SCOPED" else 1)

