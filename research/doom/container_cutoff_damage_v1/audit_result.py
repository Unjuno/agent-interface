import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/"result.json").read_text())
assert r["schema"]=="real-map01-cutoff-cancel-motor-comparison-v1"
d=r["conditions"]["damage_exposure"]
assert all(d[m]["n"]==3 for m in ("owner_deadline","explicit_cancel","no_capture_motor"))
assert d["owner_deadline"]["median_target_to_verified_empty_ms"] < d["explicit_cancel"]["median_target_to_verified_empty_ms"]
assert d["no_capture_motor"]["median_target_to_verified_empty_ms"] < d["explicit_cancel"]["median_target_to_verified_empty_ms"]
a=r["conditions"]["attack_useful"]
for m in ("owner_deadline","explicit_cancel","no_capture_motor"):
    assert a[m]["kill_count"]==1 and a[m]["death_count"]==0 and a[m]["map_exit"] is False
assert r["hard_gates"]["terminal_score_agreement"]=="PASS_12_OF_12"
assert r["hard_gates"]["verified_empty_release"]=="PASS_12_OF_12"
assert r["decision"]["gameplay_efficacy"]=="NOT_ESTABLISHED"
print("PASS retained cutoff comparison audit")
