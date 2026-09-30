import json,platform,sys
from pathlib import Path
from model import CASES,evaluate
SOURCE_MAIN="8265c1a19cbba7ab0f5316f27bdb59509269399d"
def build_raw():
    rows=[{"case_id":n,"manifest":c,"argument_only_admitted":True,**evaluate(c),"dispatched":False,"authority_minted":False,"external_effect":False} for n,c in CASES.items()]
    return {"allocation":"effect-row-composition-5366-t1-20260930-01","source_main":SOURCE_MAIN,"runtime":{"python":platform.python_version(),"platform":platform.platform()},"rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: runner.py RAW.json")
    p=Path(sys.argv[1])
    if p.exists():raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    raw=build_raw();p.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"RAW_WRITTEN","rows":len(raw["rows"])}))
