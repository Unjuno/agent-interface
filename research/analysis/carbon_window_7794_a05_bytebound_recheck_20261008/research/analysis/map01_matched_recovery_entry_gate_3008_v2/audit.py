#!/usr/bin/env python3
import itertools, json, pathlib, sys
FIELDS = ["physical_task_effect_endpoint", "task_effect_contract", "matched_arm", "arm_bound_audit", "terminal_integrity"]
def decide(row): return "AUTHORIZE" if all(row[k] for k in FIELDS) else "HOLD"
def main(d):
    data=json.loads((pathlib.Path(d)/"raw.json").read_text()); vectors=data["vectors"]; controls=data["controls"]
    expected=[dict(zip(FIELDS,b)) for b in itertools.product((False,True), repeat=5)]
    assert len(vectors)==32 and len(controls)==5
    assert all(v["decision"]==decide(v) for v in vectors+controls)
    assert sum(v["decision"]=="AUTHORIZE" for v in vectors)==1
    assert all(c["decision"]=="HOLD" for c in controls)
    assert all(all(v[k]==e[k] for k in FIELDS) for v,e in zip(sorted(vectors,key=lambda x:tuple(x[k] for k in FIELDS)), sorted(expected,key=lambda x:tuple(x[k] for k in FIELDS))))
    print("PASS_AUDIT rows=37 vectors=32 authorize=1 current=HOLD controls=5/5")
if __name__ == "__main__": main(sys.argv[1])
