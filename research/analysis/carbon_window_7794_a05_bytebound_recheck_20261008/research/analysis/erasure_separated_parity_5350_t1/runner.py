import json,platform,sys
from pathlib import Path
from model import CASES,evaluate
SOURCE_MAIN="e81cbac968752791678d22a4de3f2d276497d614"
def build_raw():
    rows=[{"case_id":n,"inputs":c,**evaluate(c),"external_effect":False} for n,c in CASES.items()]
    return {"allocation":"erasure-separated-parity-5350-t1-20260930-01","source_main":SOURCE_MAIN,"runtime":{"python":platform.python_version(),"platform":platform.platform()},"rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: runner.py RAW.json")
    p=Path(sys.argv[1])
    if p.exists():raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    raw=build_raw();p.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"RAW_WRITTEN","rows":len(raw["rows"])}))
