"""Compare accepted-first FIFO on current main and proposed PR #7589 code."""
import copy
import json
from pathlib import Path
import types

import wait_test_main_c107 as main_test
import wait_test_pr7589 as pr_test

ROOT = Path(__file__).parent
accepted = {"event": "accepted", "id": "cover-0", "accepted_ns": 100}
hard = {"event": "observation", "sequence": 9, "health": 65, "hard_floor": 73}


def run_case(test_module, source_name, use_cover_helper):
    test_module.SOURCE = ROOT / source_name
    invalidation = {"reason": "hard_health_loss", "sequence": 9}
    seen = []

    def observe(row):
        seen.append(row["sequence"])
        return invalidation if row.get("sequence") == 9 else None

    monitor = types.SimpleNamespace(observe=observe)
    wait, latest = test_module.extract_wait(test_module.Process(None),
                                            [copy.deepcopy(accepted), copy.deepcopy(hard)])
    if use_cover_helper:
        result = test_module.extract_cover_wait_helper()(wait, "cover-0", monitor)
    else:
        result = wait(lambda row: row["event"] in ("accepted", "rejected") and
                      (row.get("id") == "cover-0" or row["event"] == "rejected"))
    latest_at_accept = latest()
    seen_at_accept = list(seen)
    assert result["event"] == "accepted"
    assert latest_at_accept is None
    assert seen_at_accept == []

    # Both frozen caller paths start the planner before their next monitored wait.
    planner_started = True
    observed = wait(lambda row: row["event"] == "terminal", timeout=.2,
                    observation_monitor=monitor)
    assert observed["event"] == "policy_invalidation"
    assert seen == [9]
    assert latest() == hard
    return {
        "source": source_name,
        "accepted_returned": result,
        "latest_at_accept_return": latest_at_accept,
        "monitor_sequences_at_accept_return": seen_at_accept,
        "planner_started_before_invalidation_observed": planner_started,
        "monitor_sequences_after_next_wait": seen,
        "invalidation": observed["invalidation"],
        "latest_after_next_wait": latest(),
        "caller_sequence": ["accepted_return", "decision_artifact_prepare",
                            "planner_turn_start", "next_monitor_wait"]
    }


cases = {
    "current_main": run_case(main_test, "controller_main_c107.py", False),
    "pr_7589": run_case(pr_test, "controller_pr7589.py", True)
}
raw = {
    "events": [accepted, hard],
    "cases": cases,
    "status": "FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR",
    "scope": "deterministic synthetic FIFO/source-order construction only"
}
(ROOT / "raw_v3.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
(ROOT / "RESULT_v3.json").write_text(json.dumps({
    "status": raw["status"],
    "current_main_planner_starts_before_hard_invalidation_observed": True,
    "pr_7589_planner_starts_before_hard_invalidation_observed": True,
    "hard_event_eventually_observed_in_both_cases": True,
    "live_allocation": False,
    "task_effect": False
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps(raw, indent=2))
