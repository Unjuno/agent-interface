from __future__ import annotations
import argparse, importlib.util, json, os, platform, sys, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load_backend(path,name):
    base=types.ModuleType("doom_typed_release_backend_v1")
    class Previous: pass
    base.Backend=Previous; base.suite=object()
    owner_module=types.ModuleType("input_owner_v13")
    class InputOwner: pass
    owner_module.InputOwner=InputOwner
    sys.modules["doom_typed_release_backend_v1"]=base
    sys.modules["input_owner_v13"]=owner_module
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module.Backend
def make_cleanup(s):
    return {"event":"owner_release","reason":"cancelled","verified":True,"keys_down":[],"buttons_down":[],"per_key_release_measurements":[{
        "actuation_id":s["actuation_id"],"owner_id":s["owner_id"],"intent_token":s["intent_token"],"key":s["key"],"edge":"up",
        "classification":"CONFIRMED_PHYSICAL_UP","identity_status":"RETIRED","release_attempted":True,
        "bracket":{"owner_id":s["owner_id"],"intent_token":s["intent_token"],"key":s["key"],"status":"CONFIRMED_PHYSICAL_UP",
                   "physical_up_interval":s["cleanup_interval"],"grants_input_authority":False,"application_consumption_observed":False},
        "pre_sample":{"available":True,"error":None,"down":True,"started_ns":95,"finished_ns":100},
        "post_sample":{"available":True,"error":None,"down":False,"started_ns":108,"finished_ns":110},
        "release_request_ns":102,"sync_return_ns":108,"grants_input_authority":False,"application_consumption_observed":False}] }
def run_one(backend_cls,s):
    cleanup=make_cleanup(s)
    class Owner:
        owner_id=s["owner_id"]
        def __init__(self): self.records=[];self.physical=set()
        def call(self,operation,lease,key):
            if operation=="down":
                self.physical.add(key);self.records.append(cleanup);self.physical.clear()
                return {"event":"input_admission","owner_id":self.owner_id,"intent_token":lease.intent_token,"key":key,
                        "physical_key_measurement":{"classification":"CONFIRMED_PHYSICAL_DOWN","identity_status":"MINTED",
                          "actuation_id":s["actuation_id"],"adapter_edge":{"edge":"down","status":"CONFIRMED_PHYSICAL_DOWN",
                          "actuation_id":s["actuation_id"],"owner_id":self.owner_id,"intent_token":lease.intent_token,"key":key,
                          "interval":s["down_interval"],"grants_input_authority":False}}}
            return {"event":"input_release_measurement","owner_id":self.owner_id,"intent_token":lease.intent_token,"key":key,
                    "physical_key_measurement":{"classification":"NOOP_ALREADY_UP","actuation_id":None,"adapter_edge":None},
                    "grants_input_authority":False,"application_consumption_observed":False}
    class Lease: intent_token=s["intent_token"]
    b=object.__new__(backend_cls);b.owner=Owner();b.lease=Lease();b.held=set();b._input_event_context=(s["program_id"],s["step"]);
    b._owner_records_cursor=0;b._active_actuations={};b._actuation_context={};b.events=[];b.emit=b.events.append
    b.raw(s["key"],True);b.raw(s["key"],False);b.drain_owner_records()
    return {"events":b.events,"owner_records":b.owner.records,"physical_keys":sorted(b.owner.physical),"held_keys":sorted(b.held),
            "authority_granted":False,"application_effect_observed":False,"os_input":False,"gui":False,"game":False,"model_calls":0}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    s=json.loads((HERE/"scenario.json").read_text());old=load_backend(HERE/"SOURCE/A02/bridge.py","bridge_a02");new=load_backend(HERE/"bridge_a03.py","bridge_a03")
    raw={"run_id":s["run_id"],"scenario":s,"baseline":run_one(old,s),"successor":run_one(new,s)}
    raw_bytes=(json.dumps(raw,sort_keys=True,indent=2)+"\n").encode();(out/"RAW.json").write_bytes(raw_bytes)
    freeze=json.loads((HERE/"FREEZE.json").read_text());fbytes=(HERE/"FREEZE.json").read_bytes()
    result={"run_id":s["run_id"],"status":"PENDING_INDEPENDENT_AUDIT","raw_sha256":__import__("hashlib").sha256(raw_bytes).hexdigest(),
      "freeze_sha256":__import__("hashlib").sha256(fbytes).hexdigest(),"baseline_invocations":1,"successor_invocations":1,
      "environment":{"in_memory_stub":True,"os_input":False,"gui":False,"game":False,"model_calls":0,
      "python_version":platform.python_version(),"image_id":os.environ.get("A03_IMAGE_ID"),"platform":os.environ.get("A03_PLATFORM")},"scope":freeze["scope"]}
    (out/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"result":result,"baseline":raw["baseline"]["events"],"successor":raw["successor"]["events"]},sort_keys=True))
if __name__=="__main__":main()
