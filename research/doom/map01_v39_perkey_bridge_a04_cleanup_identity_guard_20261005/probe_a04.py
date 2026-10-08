from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, platform, sys, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load_backend(path,name):
    base=types.ModuleType("doom_typed_release_backend_v1");base.Backend=type("Previous",(),{});base.suite=object()
    owner=types.ModuleType("input_owner_v13");owner.InputOwner=type("InputOwner",(),{})
    sys.modules["doom_typed_release_backend_v1"]=base;sys.modules["input_owner_v13"]=owner
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module.Backend
def make_state(cls,s):
    b=object.__new__(cls);identity=(s["owner_id"],s["intent_token"],s["key"])
    b._actuation_context={s["actuation_id"]:(s["program_id"],s["step"])}
    b._active_actuations={identity:s["actuation_id"]};b.held={s["key"]};b.events=[];b.emit=b.events.append
    return b
def cleanup_row(s,which="valid"):
    owner,intent,key=s["owner_id"],s["intent_token"],s["key"]
    if which=="owner": owner="owner-other"
    elif which=="intent": intent="intent-other"
    elif which=="key": key=s["mismatch_key"]
    bracket_key=s["mismatch_key"] if which=="bracket" else key
    row={"actuation_id":s["actuation_id"],"owner_id":owner,"intent_token":intent,"key":key,
         "edge":"up","classification":"CONFIRMED_PHYSICAL_UP","identity_status":"RETIRED",
         "bracket":{"owner_id":owner,"intent_token":intent,"key":bracket_key,"status":"CONFIRMED_PHYSICAL_UP",
                    "physical_up_interval":[10,12],"grants_input_authority":False}}
    return {"event":"owner_release","verified":True,"keys_down":[],"buttons_down":[],"per_key_release_measurements":[row]}
def run_one(cls,s,which):
    b=make_state(cls,s);b._emit_owner_cleanup(cleanup_row(s,which))
    return {"case":which,"events":b.events,"held":sorted(b.held),"active_count":len(b._active_actuations),"context_count":len(b._actuation_context)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);out=Path(ap.parse_args().out);out.mkdir(parents=True,exist_ok=True)
    s=json.loads((HERE/"scenario.json").read_text());old=load_backend(HERE/"SOURCE/A03/bridge_a03.py","frozen_bridge_a03");new=load_backend(HERE/"bridge_a04.py","successor_bridge_a04")
    cases=["owner","intent","key","bracket","valid"]
    baseline=[];successor=[]
    for case in cases:
        baseline.append(run_one(old,s,case));successor.append(run_one(new,s,case))
    raw={"run_id":s["run_id"],"scenario":s,"baseline":baseline,"successor":successor}
    rb=(json.dumps(raw,sort_keys=True,indent=2)+"\n").encode();(out/"RAW.json").write_bytes(rb);freeze=(HERE/"FREEZE.json").read_bytes()
    result={"run_id":s["run_id"],"status":"PENDING_INDEPENDENT_AUDIT","raw_sha256":hashlib.sha256(rb).hexdigest(),"freeze_sha256":hashlib.sha256(freeze).hexdigest(),
      "baseline_invocations":1,"successor_invocations":1,"environment":{"in_memory_stub":True,"os_input":False,"gui":False,"game":False,"model_calls":0,
      "python_version":platform.python_version(),"image_id":os.environ.get("A04_IMAGE_ID"),"platform":os.environ.get("A04_PLATFORM")},"scope":"in-memory malformed-cleanup identity boundary; no OS or GUI input"}
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"run_id":s["run_id"],"cases":cases,"baseline_contextual_counts":[sum(e["event"]=="input_release_measurement" for e in c["events"]) for c in baseline],"successor_events":[[e["event"] for e in c["events"]] for c in successor],"raw_sha256":result["raw_sha256"],"status":result["status"]},sort_keys=True))
if __name__=="__main__":main()
