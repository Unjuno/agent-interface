#!/usr/bin/env python3
"""Independent standard-library auditor; recomputes no fitted model, checks all row accounting and gates."""
import json,sys,hashlib
from pathlib import Path
def validate(d):
    assert d["allocation"]=="typed-mode-4844-seed-484401-v1"
    assert len(d["rows"])==3000 and d["n_train"]==2000
    assert set(d["blocks"])=={"all_missing_cue1","all_missing_cue4","two_missing_cues","contradictory"}
    assert not any(x["direct_unsafe"] or x["typed_unsafe"] for x in d["rows"])
    for name,s in d["blocks"].items():
        rows=[r for r in d["rows"] if r["block"]==name]
        assert s["n"]==len(rows)
        for arm in ("direct","typed"):
            assert s[f"{arm}_wrong"]==sum(r[f"{arm}_wrong"] for r in rows)
            assert abs(s[f"{arm}_coverage"]-sum(r[f"{arm}_coverage"] for r in rows)/len(rows))<1e-12
    assert d["full_observation_control"]["rows"]==5
    assert d["full_observation_control"]["correct"] and d["full_observation_control"]["direct_equals_typed"]
    assert d["unknown_control"]["direct_abstains"] and d["unknown_control"]["typed_abstains"]
    assert d["contradictory_control"]["direct_abstains"] and d["contradictory_control"]["typed_abstains"]
p=Path(sys.argv[1]); b=p.read_bytes(); d=json.loads(b)
assert hashlib.sha256(b).hexdigest()==sys.argv[2]
validate(d)
checks=0
for key,val in [("allocation","mutated"),("n_train",1999)]:
    m=dict(d);m[key]=val
    try: validate(m)
    except AssertionError: checks+=1
assert checks==2
print(json.dumps({"pass":True,"errors":[],"rows":len(d["rows"]),"corruption_controls_rejected":checks,"result_sha256":hashlib.sha256(b).hexdigest()},sort_keys=True))

