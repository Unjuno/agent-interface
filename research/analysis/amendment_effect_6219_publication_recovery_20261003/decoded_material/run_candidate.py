import json,sys
from pathlib import Path
from candidate import run
from candidate import ALLOCATION, MAIN_SHA
root=Path(__file__).resolve().parent
out=Path(sys.argv[1]).resolve()
if out.exists(): raise SystemExit("STOP_OUTPUT_COLLISION")
fixture=json.loads((root/"fixture_public.json").read_text(encoding="utf-8"))
if fixture.get("allocation")!=ALLOCATION or fixture.get("main_sha")!=MAIN_SHA:
 raise SystemExit("STOP_ALLOCATION_OR_MAIN_MISMATCH")
raw=run(fixture)
out.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"allocation":raw["allocation"],"rows":len(raw["rows"]),"output":str(out)}))
