"""Freeze live binding-resolved framed intents before fresh OpenTTD input."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-framed-intents-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_framed_intents_v1.py",
        "run_openttd_framed_intents_v1.py", "framed_pointer_intent_v1.py",
        "coordinate_frame_transform_v1.py", "executor_v4.py", "session_v26.py",
        "target_guard_from_paths_v1.py", "pointer_socket_entry_v14.py",
        "event_socket_v11.py", "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py", "session_v25.py",
        "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
        "results/openttd-target-guard-transform-04/report.json",
        "results/openttd-target-guard-transform-04/audit.json"]
    task = ["openttd_task/interactive_l_target_guard_v5.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py", "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut", "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav"]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-framed-intents-01", "seed": 991004,
        "source_geometry": [129, 40, 1024, 720],
        "expected_live_target_geometry": [65, 40, 1152, 720],
        "order": ["repeat", "target"],
        "allocations": [
            {"name": "repeat", "repeat": True,
             "expected_reason": "target_not_reached", "expected_success": False},
            {"name": "target", "repeat": False,
             "expected_reason": "met", "expected_success": True}],
        "intent_contract": "runner sends only original1024 coordinates with explicit screen_chrome/window_content frames; executor resolves click, drag and condition boxes from the latest stable target binding before whole-program validation",
        "primary_endpoint": "runtime resolution records target geometry and correct translations, repeat stops, target completes, and both agree with the independent engine score",
        "failure_policy": "retain first result in declared order; no runner coordinate transform, visual calibration, retry or replacement after launch",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "one fresh scripted seed991004 positive/repeat pair at1152x720 using runtime-resolved source-frame intents and independent engine score; no model, new save, human, token or general frame-selection claim"}
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
