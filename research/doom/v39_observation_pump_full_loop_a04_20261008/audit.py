"""Read-only audit for the one-shot A04 result and frozen source identity."""
import hashlib
import json
import subprocess
from pathlib import Path

from candidate import FREEZE, pinned_source

HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


require(RESULT["schema"] == "issue59-v39-observation-pump-full-loop-result-a04",
        "unexpected result schema")
require(RESULT["main_commit"] == FREEZE["main_commit"], "result/freeze commit mismatch")
for name, spec in FREEZE["sources"].items():
    raw = pinned_source(name)
    blob = subprocess.check_output(
        ["git", "-C", str(next(p for p in HERE.parents if (p / ".git").exists())),
         "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
    require(hashlib.sha256(raw).hexdigest() == spec["sha256"], f"{name} sha256 mismatch")
    require(blob == spec["git_blob"], f"{name} git blob mismatch")

cases = {case["case"]: case for case in RESULT["cases"]}
healthy = cases["healthy_completion"]
terminals = healthy["cover_terminals"]
require([row["id"] for row in terminals] == [
    "cover-0", "cover-0-renew-0", "cover-0-renew-1"],
    "healthy run did not validate each matching cover terminal")
require(healthy["submitted"] == ["cover-0-renew-0", "cover-0-renew-1"],
        "healthy run did not perform exactly two matching renewals")
done_indexes = [i for i, row in enumerate(healthy["events"])
                if row.get("event") == "planner_future_poll" and row.get("done") is True]
require(len(done_indexes) == 1, "expected exactly one completion poll")
require(not any(row.get("event") == "cover_renewed"
                for row in healthy["events"][done_indexes[0] + 1:]),
        "cover renewed after planner completion was observed")
received = [row for row in healthy["events"] if row.get("event") == "monitor_received"]
require([row["sequence"] for row in received] == [2, 3, 4],
        "healthy observations were not all dispatched")
require(all(row["future_pending"] for row in received),
        "healthy observation was not dispatched while planner pending")
for terminal in terminals:
    require(terminal["release"] == {
        "verified": True, "keys_down": [], "buttons_down": []},
        "healthy terminal did not report verified empty release")

invalid = cases["invalidation"]
events = invalid["events"]
cancel_flush = next(i for i, row in enumerate(events)
                    if row.get("event") == "executor_cancel_flush")
interrupt = next(i for i, row in enumerate(events)
                 if row.get("event") == "planner_interrupt_transport")
require(cancel_flush < interrupt, "cancel flush did not precede interrupt transport")
require(invalid["terminal"]["release"] == {
    "verified": True, "keys_down": [], "buttons_down": []},
    "invalidation terminal did not report verified empty release")
require(invalid["terminal"]["status"] == "cancelled",
        "invalidation did not close with a cancelled terminal")

print(json.dumps({
    "status": "PASS_AUDIT_A04_CONSTRUCTION_ONLY",
    "main_commit": FREEZE["main_commit"],
    "sources_verified": len(FREEZE["sources"]),
    "healthy_matching_terminals": [row["id"] for row in terminals],
    "healthy_renewals": healthy["submitted"],
    "completion_poll_index": done_indexes[0],
    "observations_dispatched_while_pending": [row["sequence"] for row in received],
    "invalidation_cancel_flush_before_interrupt_transport": True,
    "scope": "Synthetic source-slice construction; no producer, game, GUI, OS input, or task effect.",
}, sort_keys=True))
