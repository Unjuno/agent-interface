"""Freeze cross-domain point contract before fresh OpenTTD execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-point-contract-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    live = [
        "preregister_openttd_point_contract_pair_v1.py",
        "run_openttd_point_contract_pair_v1.py", "pointer_socket_entry_v18.py",
        "event_socket_v11.py", "point_target_contract_v2.py",
        "point_target_contract_schema_v1.json",
        "point_target_reference_responder_v1.txt",
        "target_handle_model_runner_v2.py", "session_v33.py",
        "model_point_target_v1.py", "session_v32.py", "observe_target_handle_v1.py",
        "session_v31.py", "session_v30.py", "session_v29.py", "session_v28.py",
        "session_v26.py", "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "local_target_guard_postcondition_v1.py", "session_v25.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "executor_v4.py",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
    ]
    task = [
        "openttd_task/interactive_l_point_target_v1.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py",
        "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut",
        "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav",
    ]
    plan = {
        "status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-point-contract-pair-01", "seed": 991004,
        "execution_order": [
            {"name": "transient-target", "transient_target": True, "seed": 991004},
            {"name": "stable", "transient_target": False, "seed": 991004},
        ],
        "task": "model-ground Road Construction, then build the guarded five-tile L",
        "common": (
            "same save/task/model prompt, Luna-low and current1024x720 image; model "
            "authors source pixel point and motion; runtime fixed24x14 region; one call/case"),
        "stable": (
            "mint exact point target, request surface move[20,8], use observed actual delta "
            "for handle/path/condition, complete independent guarded L score"),
        "transient_target": (
            "after model return click known Road Construction opener and observe; exact "
            "source patch must change and mint must refuse before a handle is created"),
        "promotion": (
            "strict contract2/2 and input range<=128; stable moved handle plus all engine "
            "checks; transient selected-target patch refuses before handle"),
        "failure_policy": "retain both first sessions; no retry or prompt/point/frame/size/order repair",
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": (
            "two fresh same-save seed991004 OpenTTD X11 sessions and two Luna-low image "
            "calls; one scripted guarded L plus selected-target negative; independent engine "
            "score; no unseen task, causal speed, cost, broad token or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
