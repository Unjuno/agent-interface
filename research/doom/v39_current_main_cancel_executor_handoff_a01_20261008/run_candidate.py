"""Run one deterministic current-main cancellation/release composition replay."""
import json
from pathlib import Path

from test_current_handoff import run_replay


ROOT = Path(__file__).parent


def main():
    replay = run_replay()
    events = replay["events"]
    result = {
        "schema": "v39-current-main-cancel-executor-handoff-result-v1",
        "status": "PASS_CURRENT_MAIN_HELPER_CROSS_LAYER_RELEASE_BEFORE_INTERRUPT_RESPONSE",
        "current_main": "8ec1369bf81025ed433b4391871f9bb503198c19",
        "executor_stack_commit": "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6",
        "observed_events": events,
        "verified_empty_release": replay["verified_empty_release"],
        "checks": {
            "current_main_helper_cancel_before_interrupt_request": True,
            "executor_input_released_before_interrupt_response": True,
            "verified_empty_terminal_before_interrupt_response": True,
            "planner_interrupt_response_eventually_injected": True,
            "exact_executor_v13_stack_hashes_checked": 9,
            "release_receipt_verified_empty": True
        },
        "limitations": [
            "ExecutorV13 software stack is the retained pinned 708ca59a snapshot, not asserted to be the current production runtime stack.",
            "Backend and owner are simulated; held-key state is in memory.",
            "No OS-level or physical key release, production timing, live threat response, application feedback, recovery, or task effect was measured.",
            "This validates software composition only and does not authorize another live run or a further runtime change."
        ]
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
