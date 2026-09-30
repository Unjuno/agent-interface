import json,platform,sys
from pathlib import Path
from model import CASES,POLICIES,evaluate
SOURCE_MAIN="bbeee4da02285281e960334f8babefc2d7070358"
def build_raw():
    rows=[{"case_id":n,"policy":p,"inputs":c,**evaluate(c,p),"authority_minted":False,"external_effect":False} for n,c in CASES.items() for p in POLICIES]
    return {"allocation":"quiescent-epoch-binding-5361-t1-20260930-01","source_main":SOURCE_MAIN,"runtime":{"python":platform.python_version(),"platform":platform.platform()},"rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: runner.py RAW.json")
    p=Path(sys.argv[1])
    if p.exists(): raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    raw=build_raw();p.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"RAW_WRITTEN","rows":len(raw["rows"])}))
