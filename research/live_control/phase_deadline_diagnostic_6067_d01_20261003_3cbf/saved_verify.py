"""Saved-only custody replay and exactly ten corruption controls; no native calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import auditor

HERE = Path(__file__).resolve().parent
CONTROL_NAMES = ["due_bool","counter_bool","native_clock","pixel_hash","sleep_request","omitted_sleep","optional_grammar","fake_decode",
                 "stream_bool_join","duplicate_json","nonfinite_json","missing_plan_cell"]

def controls(raw,plan):
    original = auditor.stream(Path(raw)/"d000/record/frames.jsonl")[0]
    results = []
    for name in CONTROL_NAMES:
        f = copy.deepcopy(original)
        def exercise():
            if name=="stream_bool_join": auditor.join({"index":False},{"index":0},"typed frame stream"); return
            if name=="duplicate_json": auditor.parse('{"x":0,"x":0}'); return
            if name=="nonfinite_json": auditor.parse('{"x":NaN}'); return
            if name=="missing_plan_cell":
                p=copy.deepcopy(plan); p["cells"].pop(); auditor.check_plan(p); return
            if name=="due_bool": f["due_ns"]=True
            elif name=="counter_bool": f["post"]["cpu_stat"]["nr_periods"]=False
            elif name=="native_clock": f["start_ns"]=f["pre"]["begin_ns"]
            elif name=="pixel_hash": f["pixel_sha256"]="0"*64
            elif name=="sleep_request":
                if not f["wait"]["sleeps"]: raise RuntimeError("required actual sleep absent; do not count a control")
                f["wait"]["sleeps"][0]["requested_ns"]=1
            elif name=="fake_decode": f["decoded"]={"id":1,"color":16711680}
            elif name=="omitted_sleep": f["wait"]["sleeps"]=[]
            elif name=="optional_grammar": f["post"]["schedstat"]={"available":True,"raw":"garbage","error":None}
            auditor.frame_metrics(f,original["due_ns"])
        try:
            exercise()
        except ValueError as e:
            results.append({"name":name,"status":"REJECTED","error":str(e)})
        else:
            raise ValueError("ineffective control: "+name)
    return {"source_frame":"d000/record/frames.jsonl index0","source_frame_sha256":
            hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
            "controls":results,"rejected":len(results),"native_replays":0}

def verify(manifest=True):
    if manifest:
        m=auditor.read(HERE/"MANIFEST.json")
        actual={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in HERE.rglob("*") if p.is_file() and p.name!="MANIFEST.json"
                and "__pycache__" not in p.parts}
        auditor.join(actual,m["files_sha256"],"complete package manifest")
    freeze=auditor.read(HERE/"FREEZE.json")
    for name,digest in freeze["source_sha256"].items():
        auditor.require(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,"frozen source")
    plan=auditor.read(HERE/"plan.json")
    result=auditor.audit(HERE/"raw",plan,freeze)
    auditor.join(result,auditor.read(HERE/"audit/RESULT.json"),"saved independent result")
    corruption=controls(HERE/"raw",plan)
    auditor.join(corruption,auditor.read(HERE/"audit/controls.json"),"saved effective controls")
    print(json.dumps({"status":result["status"],"cells":result["valid_cells"],
                      "frames":result["native_frames"],"rejected":corruption["rejected"],
                      "manifest":manifest,"native_replays":0},sort_keys=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--controls-out",type=Path)
    ap.add_argument("--no-manifest",action="store_true")
    a=ap.parse_args()
    if a.controls_out:
        value=controls(HERE/"raw",auditor.read(HERE/"plan.json"))
        with a.controls_out.open("x") as f:
            json.dump(value,f,sort_keys=True,indent=2); f.write("\n")
    else: verify(not a.no_manifest)
if __name__=="__main__": main()
