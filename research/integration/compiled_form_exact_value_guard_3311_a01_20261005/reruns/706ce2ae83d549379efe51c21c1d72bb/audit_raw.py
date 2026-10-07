import json
from pathlib import Path
p = Path(__file__).with_name("raw-differential.json")
r = json.loads(p.read_text(encoding="utf-8"))
assert r["experiment_id"] == "compiled-form-guard-differential-3311-20261005-01"
assert len(r["input_rows"]) == 3
assert all(x["field_pixels_changed"] is True and x["field_value_matches_task"] is False for x in r["input_rows"][1:])
v1, v2 = r["results"]
assert v1["version"] == "v1" and v1["actions"] == ["enter_exact_token", "activate_submit"]
assert v1["outcome"] == "TASK_SUCCEEDED" and v1["reason"] == "method_complete"
assert v2["version"] == "v2" and v2["actions"] == ["enter_exact_token"]
assert v2["outcome"] == "SAFE_YIELD" and v2["reason"] == "effect_failed"
assert all(all(e["release_verified"] is True for e in x["receipt"]["critical_events"] if e.get("event") == "action_terminal") for x in (v1, v2))
print(json.dumps({"audit": "PASS_RAW_RECONSTRUCTION", "experiment_id": r["experiment_id"], "v1": {"outcome":v1["outcome"],"actions":v1["actions"]}, "v2": {"outcome":v2["outcome"],"actions":v2["actions"]}, "scope": "synthetic runtime branch behavior; no live GUI/model/effect/economy claim"}, sort_keys=True, indent=2))
