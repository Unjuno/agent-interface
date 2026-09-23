"""Freeze cross-domain observe-target use on the guarded OpenTTD L task."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-observe-target-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = [
        "preregister_openttd_observe_target_live_v1.py",
        "run_openttd_observe_target_live_v1.py", "pointer_socket_entry_v17.py",
        "event_socket_v11.py", "session_v32.py", "observe_target_handle_v1.py",
        "session_v31.py", "session_v30.py", "session_v29.py", "session_v28.py",
        "session_v26.py", "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "local_target_guard_postcondition_v1.py", "session_v25.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "executor_v4.py",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
    ]
    task = [
        "openttd_task/interactive_l_observe_target_v1.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py",
        "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut",
        "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav",
    ]
    plan = {
        "status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-observe-target-live-01", "seed": 991004,
        "task": "build the complete five-tile guarded L from A through B to C",
        "handle": {"alias": "road_construction_opener",
                   "box": [812, 43, 16, 16], "offset": [8, 8],
                   "coordinate_frame": "window_content"},
        "combined_boundary": (
            "capture one exact fresh observation, resolve the alias on that same "
            "identity, then revalidate again during later input admission"
        ),
        "primary_endpoint": (
            "local first-segment target/guard condition met; continuation starts; "
            "independent target roads, ordered connections, forbidden row and "
            "surrounding guard checks all true"
        ),
        "failure_policy": "retain first allocation; no rerun, region or coordinate repair",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": (
            "one fresh scripted seed991004 OpenTTD X11 cross-domain integration with "
            "independent engine score; development-known geometry; no model, token, "
            "latency distribution, human-speed or generalization claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
