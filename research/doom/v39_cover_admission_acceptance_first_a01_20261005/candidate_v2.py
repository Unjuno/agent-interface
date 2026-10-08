"""Candidate v2: sample latest exactly at the acceptance-return boundary."""
import json
from pathlib import Path
import types

from wait_test_pr7589 import Process, extract_cover_wait_helper, extract_wait

ROOT = Path(__file__).parent
invalidation = {"reason": "hard_health_loss", "sequence": 9}
seen = []


def observe(row):
    seen.append(row["sequence"])
    return invalidation if row.get("sequence") == 9 else None


monitor = types.SimpleNamespace(observe=observe)
accepted = {"event": "accepted", "id": "cover-0", "accepted_ns": 100}
hard = {"event": "observation", "sequence": 9, "health": 65, "hard_floor": 73}
wait, latest = extract_wait(Process(None), [accepted, hard])
accept = extract_cover_wait_helper()

accepted_result = accept(wait, "cover-0", monitor)
latest_at_accept_return = latest()
seen_at_accept_return = list(seen)
assert accepted_result is accepted
assert latest_at_accept_return is None
assert seen_at_accept_return == []

# The frozen caller prepares artifacts and starts the planner before its next
# monitor-enabled wait. Event observation then requests cancellation.
caller_steps = ["accepted_return", "decision_artifact_prepare", "planner_turn_start"]
planner_started = True
observed = wait(lambda row: row["event"] == "terminal", timeout=.2,
                observation_monitor=monitor)
assert observed["event"] == "policy_invalidation"
invalidation_seen = observed["invalidation"]
assert seen == [9]
assert latest() is hard

raw = {
    "events": [accepted, hard],
    "accepted_returned": accepted_result,
    "latest_observation_at_accept_return": latest_at_accept_return,
    "monitor_sequences_at_accept_return": seen_at_accept_return,
    "caller_steps_before_next_monitored_wait": caller_steps,
    "planner_started_before_hard_invalidation_observed": planner_started,
    "monitor_sequences_after_next_wait": seen,
    "invalidation": invalidation_seen,
    "latest_observation_after_next_wait": latest(),
    "status": "FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR",
    "scope": "synthetic FIFO/source-order construction only"
}
(ROOT / "raw_v2.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
(ROOT / "RESULT_v2.json").write_text(json.dumps({
    "status": raw["status"],
    "planner_started_before_invalidation_observed": True,
    "hard_event_eventually_observed": True,
    "live_allocation": False,
    "task_effect": False
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps(raw, indent=2))
