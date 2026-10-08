"""Freeze the second-resolution replication before fresh input."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-transform-04"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_target_guard_transform_v4.py",
        "run_openttd_target_guard_transform_v4.py",
        "run_openttd_target_guard_transform_v1.py", "target_guard_from_paths_v1.py",
        "pointer_socket_entry_v13.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py", "received_exchange_v2.py",
        "session_v25.py", "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
        "results/openttd-target-guard-transform-03/report.json",
        "results/openttd-target-guard-transform-03/audit.json"]
    task = ["openttd_task/interactive_l_target_guard_v4.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py", "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut", "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav"]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-target-guard-transform-04", "seed": 991004,
        "source_resolution": "1024x720", "held_out_resolution": "1152x720",
        "predicted_source_pointer_geometry": [129, 40, 1024, 720],
        "predicted_target_pointer_geometry": [65, 40, 1152, 720],
        "coordinate_frames": {
            "screen_chrome_translation": {"dx": 0, "dy": 0},
            "viewport_content_translation": {"dx": -64, "dy": 0}},
        "order": ["target", "repeat"],
        "allocations": [
            {"name": "target", "repeat": False,
             "expected_reason": "met", "expected_success": True},
            {"name": "repeat", "repeat": True,
             "expected_reason": "target_not_reached", "expected_success": False}],
        "fixed_condition": {"pixel_delta_threshold": 24,
            "minimum_target_changed_pixels": 120, "maximum_guard_changed_pixels": 20,
            "required_samples": 2, "bounded_settle_before": True},
        "primary_endpoint": "without observing the new viewport first, predicted frame-specific transforms reproduce target completion and repeat suppression at 1152x720",
        "failure_policy": "retain first result in declared reverse order; no visual calibration, coordinate correction, retry or replacement after launch",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "one fresh scripted second-resolution replication on seed991004, predicted from the frame-specific transform; no model, unseen task, human, token or broad transform claim"}
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
