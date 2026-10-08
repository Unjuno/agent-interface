"""Freeze a fresh changed-save pair using boxes derived from pointer paths."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-geometry-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_target_guard_geometry_v1.py",
        "run_openttd_target_guard_geometry_v1.py", "target_guard_from_paths_v1.py",
        "pointer_socket_entry_v11.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py", "received_exchange_v2.py",
        "session_v25.py", "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
        "results/openttd-target-guard-derived-archive-01/report.json"]
    task = ["openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py", "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut", "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav"]
    first = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
    continuation = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-target-guard-geometry-01", "seed": 991004,
        "order": ["wrong-row", "target"],
        "allocations": [
            {"name": "wrong-row", "first_y_offset": -16,
             "expected_reason": "target_not_reached", "expected_success": False},
            {"name": "target", "first_y_offset": 0,
             "expected_reason": "met", "expected_success": True}],
        "condition_first_path": first, "continuation_path": continuation,
        "box_derivation": "12x8 boxes centered on first-path points; guard boxes centered on continuation points after the bounded shared corner",
        "fixed_condition": {"pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "bounded_settle_before": True},
        "primary_endpoint": "path-derived boxes stop shifted wrong-row before B-to-C and admit target B-to-C to independent changed-save L success",
        "failure_policy": "retain first outcome of both ordered allocations; no retry or replacement",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "one fresh scripted seed991004 changed-save OpenTTD pair with action-derived visual boxes and independent engine score; screen layout and path are development-known; no model, held-out visual layout, human, token or generalization claim"}
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
