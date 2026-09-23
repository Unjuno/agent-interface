"""Freeze the one-click OpenTTD driver correction before fresh input."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-live-02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_target_guard_live_v2.py", "run_openttd_target_guard_live_v2.py",
        "pointer_socket_entry_v10.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py", "received_exchange_v2.py",
        "session_v25.py", "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py"]
    task = ["openttd_task/interactive_l_target_guard_v1.py", "openttd_task/guarded_l_score_v1.py",
        "openttd_task/observer_l_v1/common.nut", "openttd_task/observer_l_v1/main.nut",
        "openttd_task/observer_l_v1/info.nut", "openttd_task/results/l-geometry-01/baseline.sav"]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-target-guard-live-02", "order": ["wrong-row", "target"],
        "allocations": [
            {"name": "wrong-row", "first_y": 224, "expected_reason": "target_not_reached",
             "expected_success": False},
            {"name": "target", "first_y": 240, "expected_reason": "met",
             "expected_success": True}],
        "single_change_from_retained_v1": "prepend pointer_click(820,51) to open Road Construction before pointer_click(709,91)",
        "fixed_condition": {"pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "bounded_settle_before": True},
        "primary_endpoint": "wrong-row stops before B-to-C and independently fails; target admits B-to-C and independently completes the guarded L",
        "secondary_endpoints": ["first drag issued to local condition", "condition to terminal",
                                "durable calls", "verified releases", "exact runtime frames"],
        "failure_policy": "retain first outcome of both ordered allocations; no retry or replacement",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "matched scripted fresh seed991003 OpenTTD pair after one-click driver correction with independent engine score; no model call, model authorship, human comparison, token or generalization claim"}
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
