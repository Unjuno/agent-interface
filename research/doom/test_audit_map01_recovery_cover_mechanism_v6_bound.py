from __future__ import annotations
import json, tempfile
from pathlib import Path
from audit_map01_recovery_cover_mechanism_v6_bound import binding_failures

def build():
    root=Path(tempfile.mkdtemp())
    summary={}
    for i in range(1,4):
        summary[f"pair{i}"]={"coast_no_retained_input_upper_ns":600_000_000,
                             "recovery_no_retained_input_upper_ns":570_000_000}
        for arm,value in (("coast",600_000_000),("recovery",570_000_000)):
            d=root/f"pair{i}"/arm; d.mkdir(parents=True)
            (d/"arm-summary.json").write_text(json.dumps({"input_bounds":{"no_retained_input_upper_bound_ns":value}}))
    (root/"summary.json").write_text(json.dumps(summary))
    return root

def run():
    root=build()
    assert binding_failures(root)==[]
    for i in range(1,4):
        for arm,key in (("coast","coast_no_retained_input_upper_ns"),("recovery","recovery_no_retained_input_upper_ns")):
            s=json.loads((root/"summary.json").read_text()); s[f"pair{i}"][key]+=1
            (root/"summary.json").write_text(json.dumps(s))
            got=binding_failures(root)
            assert got==[f"pair{i}:{arm}:{key}:summary_arm_mismatch"],got
            s[f"pair{i}"][key]-=1; (root/"summary.json").write_text(json.dumps(s))
    print("PASS_V6_BOUND_BINDINGS 6/6")
if __name__=="__main__": run()
