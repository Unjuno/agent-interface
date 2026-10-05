"""Freeze a translated-view OpenTTD target/guard pair before fresh input."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-transform-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_target_guard_transform_v1.py",
        "run_openttd_target_guard_transform_v1.py", "target_guard_from_paths_v1.py",
        "pointer_socket_entry_v12.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py", "received_exchange_v2.py",
        "session_v25.py", "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py"]
    task = ["openttd_task/interactive_l_target_guard_v3.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py", "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut", "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav"]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-target-guard-transform-01", "seed": 991004,
        "source_resolution": "1024x720", "held_out_resolution": "1280x720",
        "declared_transform": {"type": "translation", "dx": 128, "dy": 0,
            "derivation": "half of the 256px width increase; applied unchanged to toolbar controls, pointer paths and condition boxes"},
        "order": ["repeat", "target"],
        "allocations": [
            {"name": "repeat", "repeat": True,
             "expected_reason": "target_not_reached", "expected_success": False},
            {"name": "target", "repeat": False,
             "expected_reason": "met", "expected_success": True}],
        "fixed_condition": {"pixel_delta_threshold": 24,
            "minimum_target_changed_pixels": 120, "maximum_guard_changed_pixels": 20,
            "required_samples": 2, "bounded_settle_before": True},
        "primary_endpoint": "one declared translation moves controls, paths and path-derived boxes without post-launch coordinate edits; repeat stops before continuation and target independently completes",
        "failure_policy": "retain first result in declared order; no visual calibration, coordinate correction, retry or replacement after launch",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "one fresh scripted seed991004 resolution transform with path-derived boxes and independent engine score; transform is analytically declared from a development-known path; no model, unseen task, human, token or general geometry claim"}
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
