import hashlib
import json
from pathlib import Path

base = Path(__file__).parent / "out"
raw_bytes = (base / "raw.jsonl").read_bytes()
raw = [json.loads(line) for line in raw_bytes.splitlines()]
events = [json.loads(line) for line in (base / "xtest-emissions.jsonl").read_bytes().splitlines()]
by_name = {row["event"]: row for row in raw}
checks = {}

def require(name, condition):
    checks[name] = bool(condition)
    if not condition:
        raise SystemExit("FAIL: " + name)

require("single_run_source_pinned", raw[0]["source_revision"] == "f33695096b7460dc148d348d6c9a26c7815c1569")
require("p1_p2_are_distinct_process_generations", by_name["p1_minted"]["identity"] != by_name["review"]["identity"])
require("replacement_xid_differs", by_name["p1_minted"]["xid"] != by_name["review"]["new_xid"])
review = by_name["review"]
require("explicit_review_succeeded", review["row"]["status"] == "reviewed")
require("review_incremented_revision", review["new_revision"] == review["old_revision"] + 1)
require("review_changed_scope", review["new_scope"] != review["old_scope"])
old = by_name["old_alias_attempt"]
require("old_alias_refused", old["result"]["status"] == "refused")
require("old_alias_unknown_after_handoff", old["result"]["guard_checks"][0]["status"] == "MISSING")
require("old_alias_declared_no_dispatch", old["result"]["input_dispatched"] is False)
require("old_alias_backend_emission_counter_zero", old["emissions_before"] == old["emissions_after"] == 0)
fresh = by_name["fresh_alias_control"]
fresh_start = fresh["result"]["execution"]["started_ns"]
# The independently wrapped native XTEST calls all occurred after the positive-control
# dispatch began; combined with the preceding old-alias refusal and its zero counter delta,
# this bounds the earlier attempt to zero observed XTEST events.
require("all_x_test_events_after_positive_control_start", len(events) == 3 and all(e["time_ns"] >= fresh_start for e in events))
require("no_replacement_effect_before_positive_control", old["effect"] is None)
require("fresh_alias_completed", fresh["result"]["status"] == "completed")
require("fresh_control_emissions_match_hook", fresh["emissions_after"] - fresh["emissions_before"] == len(events) == 3)
effect = json.loads(fresh["effect"])
require("fresh_control_changed_p2", effect["pid"] == review["identity"]["pid"] and effect["effect"] == "clicked")
require("application_title_effect_observed", fresh["title"] == "NR3467-EFFECT-TARGET")
result = {
    "decision": "PASS_REVIEW_REVOKES_PREDECESSOR_ALIAS",
    "checks": checks,
    "raw_jsonl_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "raw_jsonl_bytes": len(raw_bytes),
    "xtest_events_sha256": hashlib.sha256((base / "xtest-emissions.jsonl").read_bytes()).hexdigest(),
    "xtest_event_count": len(events),
    "p2_effect_sha256": hashlib.sha256((base / "p2-effect.json").read_bytes()).hexdigest(),
}
(base / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
