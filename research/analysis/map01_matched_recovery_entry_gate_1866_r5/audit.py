#!/usr/bin/env python3
import itertools, json, pathlib, sys

FIELDS=("physical_task_effect_endpoint","task_effect_contract","matched_arm","arm_bound_audit","terminal_integrity")

def oracle(row):
    return "AUTHORIZE" if all(row[k] is True for k in FIELDS) else "HOLD"

def main(d):
    raw=json.loads((pathlib.Path(d)/"raw.json").read_text())
    snap=raw["snapshot"]
    assert snap["base_main"]=="b38806cd09243f7ad18deb61db44048bc3feffae"
    assert snap["previous_snapshot_comment_id"]==5778061179
    assert snap["previous_gate_source"]["git_blob"]=="fd1ddd07f4283cb60a20ed3a957dd4727b843958"
    ep=snap["new_endpoint_evidence"]
    assert ep["git_blob"]=="384328c63f75108e35b8b9126179d6bace478095"
    assert ep["decision"]=="PASS_SAME_RUN_RELEASE_TASK_EFFECT_ENDPOINT_SCOPED"
    expected=[dict(zip(FIELDS,b)) for b in itertools.product((False,True),repeat=5)]
    vectors=raw["vectors"]; controls=raw["controls"]; current=raw["current"]
    assert len(vectors)==32 and len(controls)==5
    assert all(v["decision"]==oracle(v) for v in vectors)
    assert sum(v["decision"]=="AUTHORIZE" for v in vectors)==1
    assert all(all(v[k]==e[k] for k in FIELDS) for v,e in zip(
        sorted(vectors,key=lambda x:tuple(x[k] for k in FIELDS)),
        sorted(expected,key=lambda x:tuple(x[k] for k in FIELDS))))
    assert current["decision"]=="AUTHORIZE"
    assert all(current[k] is True for k in FIELDS)
    assert all(c["decision"]=="HOLD" for c in controls)
    print("PASS_AUDIT current=AUTHORIZE vectors=32 authorize=1 controls=5/5")

if __name__=="__main__": main(sys.argv[1])
