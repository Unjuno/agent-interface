#!/usr/bin/env python3
import copy, json, sys, tempfile
from pathlib import Path
from audit import audit

def main(result_path,repo):
    base=json.loads(Path(result_path).read_text())
    assert audit(result_path,repo)["pass"]
    muts=[]
    def add(name,fn):
        x=copy.deepcopy(base);fn(x);muts.append((name,x))
    add("decision",lambda x:x.__setitem__("decision","RETAIN_FIRST_TASK_RELEVANT_FEEDBACK_SCOPED"))
    add("source_hash",lambda x:x["runs"][0].__setitem__("events_sha256","0"*64))
    add("earliest_sequence",lambda x:x["runs"][0]["plans"][0]["earliest_state_feedback"].__setitem__("sequence",999999) if x["runs"][0]["plans"][0]["earliest_state_feedback"] else x["runs"][0]["plans"][0].__setitem__("earliest_state_feedback",{"sequence":999999}))
    add("baseline",lambda x:x["runs"][0]["plans"][0]["baseline_independent"].__setitem__("health",999))
    add("stronger_effect",lambda x:x["runs"][0]["plans"][0].__setitem__("stronger_task_effect_feedback",{"fake":True}))
    rejected=[]
    with tempfile.TemporaryDirectory() as td:
        for name,obj in muts:
            p=Path(td)/f"{name}.json";p.write_text(json.dumps(obj))
            ok=not audit(p,repo)["pass"];rejected.append((name,ok));assert ok,name
    print(json.dumps({"mutations":rejected,"all_rejected":all(v for _,v in rejected)}))
if __name__=="__main__":main(sys.argv[1],sys.argv[2])
