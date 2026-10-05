"""Independent raw-outcome and source-hash audit for the follow-up."""
import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
raw = json.loads((HERE / "RAW.json").read_text(encoding="utf-8"))
tests = (HERE / raw["focused_tests"]["output_file"]).read_text(encoding="utf-8")
actual_hash = hashlib.sha256(
    (DOOM / "doom_controller_failure_cleanup_v1.py").read_bytes()).hexdigest()
count_match = re.search(r"Ran (\d+) tests? in", tests)
baseline = raw["baseline"]
candidate = raw["candidate"]
observed = candidate["observed"] or {}
checks = {
    "parent_timed_out": baseline["outcome"] == "watchdog_timeout",
    "baseline_no_receipt": baseline["receipt_exists_after_process"] is False,
    "candidate_completed": candidate["outcome"] == "completed",
    "candidate_primary_preserved": observed.get("primary_identity_preserved") is True,
    "candidate_receipt_written": observed.get("receipt_written") is True,
    "candidate_planner_timeout_recorded": observed.get("planner_close_status") == "timed_out",
    "candidate_incomplete": observed.get("cleanup_complete") is False,
    "candidate_returned_within_bound": candidate["elapsed_seconds"] <= 2.5,
    "focused_tests_passed": raw["focused_tests"]["returncode"] == 0 and
                            raw["focused_tests"]["passed"] is True and
                            count_match is not None and int(count_match.group(1)) == 31,
    "helper_hash_matches": actual_hash == raw["helper_sha256"],
}
audit = {
    "audit": "raw-only independent checks; no live GUI/game/input claims",
    "checks": checks,
    "all_pass": all(checks.values()),
    "focused_test_count": None if count_match is None else int(count_match.group(1)),
    "actual_helper_sha256": actual_hash,
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True))
raise SystemExit(0 if audit["all_pass"] else 1)
