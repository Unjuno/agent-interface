"""Freeze one same-session handle mint, surface move, revalidation and click."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-handle-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live = ["preregister_openttd_target_handle_live_v1.py",
        "run_openttd_target_handle_live_v1.py", "scoped_target_handle_v2.py",
        "scoped_target_handle_v1.py", "coordinate_frame_transform_v1.py",
        "executor_v4.py", "session_v29.py", "session_v28.py", "session_v26.py",
        "pointer_socket_entry_v16.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py",
        "received_exchange_v2.py", "session_v25.py",
        "local_target_guard_postcondition_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py"]
    task = ["openttd_task/interactive_l_target_handle_v1.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py", "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut", "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav"]
    plan = {"status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-target-handle-live-01", "seed": 991004,
        "initial_geometry": [65, 40, 1152, 720],
        "handle": {"name": "road_construction_opener", "box": [812, 43, 16, 16],
                   "coordinate_frame": "window_content", "point_offset": [8, 8],
                   "allowed_transformations": ["window_translation"]},
        "intervention": "mint from current pixels, move the same client surface +16px, acquire a fresh observation, then click only through the runtime handle",
        "primary_endpoint": "REVALIDATED with binding translation[16,0], resolved point[836,51], ordinary pointer admission, completed terminal and verified release",
        "negative_evidence": "independent road-task score is expected false because this study clicks only the toolbar opener; it is retained and must not be described as task completion",
        "failure_policy": "retain the first fresh outcome; no retry, alternate region or threshold relaxation",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": "one fresh scripted same-session OpenTTD X11 handle-lifetime case; exact textured region, test-only surface move, no model, task success, speed, token or semantic-identity claim"}
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
