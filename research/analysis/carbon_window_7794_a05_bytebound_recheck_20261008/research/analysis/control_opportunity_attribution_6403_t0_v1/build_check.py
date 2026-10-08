"""Construction-time gate and adversarial mutation checks; not formal evidence."""
import copy
import json
from pathlib import Path

from auditor import audit
from candidate import run


ROOT = Path(__file__).parent
fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
oracle = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))
baseline = run(str(ROOT / "fixture.json"))
baseline_audit = audit(fixture, oracle, baseline)
assert baseline_audit["status"] == "PASS_METHOD", baseline_audit

mutations = {}
bad = copy.deepcopy(baseline)
row = next(item for item in bad["records"] if item["trace"] == "sent_but_undelivered")
row["assessment"] = "OPPORTUNITY"
row["control_timeline_summary"]["assessment"] = "OPPORTUNITY"
mutations["sent_as_received"] = bad

bad = copy.deepcopy(baseline)
row = next(item for item in bad["records"] if item["trace"] == "accepted_with_sufficient_time")
row["control_timeline_summary"]["events"][-1]["at"] = 2
mutations["effect_moved_before_window"] = bad

bad = copy.deepcopy(baseline)
row = next(item for item in bad["records"] if item["trace"] == "accepted_with_sufficient_time")
row["control_timeline_summary"].pop("safe_override_available")
mutations["hide_safe_override"] = bad

bad = copy.deepcopy(baseline)
bad["records"][0]["control_timeline_summary"]["oracle_label"] = "NO_OPPORTUNITY"
mutations["oracle_leak"] = bad

bad = copy.deepcopy(baseline)
bad["non_authoritative_negative_controls"][0]["authoritative"] = True
mutations["promote_negative_control"] = bad

bad = copy.deepcopy(baseline)
bad["records"][0]["actor_outcome_summary"]["claim"] = fixture["negative_controls"][0]["claim"]
mutations["show_negative_control"] = bad

results = {name: audit(fixture, oracle, output) for name, output in mutations.items()}
undetected = [name for name, result in results.items() if result["status"] != "FAIL_METHOD"]
assert not undetected, f"undetected corruptions: {undetected}"
print(json.dumps({"status": "BUILD_CHECK_PASS", "baseline": baseline_audit,
                  "mutations_rejected": sorted(results)}, sort_keys=True, separators=(",", ":")))
