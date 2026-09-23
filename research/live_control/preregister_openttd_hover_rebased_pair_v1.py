"""Freeze persistent target rebasing before fresh OpenTTD execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-hover-rebased-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    live = [
        "preregister_openttd_hover_rebased_pair_v1.py",
        "run_openttd_hover_rebased_pair_v1.py",
        "run_openttd_hover_target_pair_v1.py", "pointer_socket_entry_v19.py",
        "event_socket_v11.py", "session_v34.py", "session_v33.py",
        "model_point_target_v1.py", "session_v32.py", "observe_target_handle_v1.py",
        "session_v31.py", "session_v30.py", "session_v29.py", "session_v28.py",
        "session_v26.py", "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "local_target_guard_postcondition_v1.py", "session_v25.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "executor_v4.py",
        "openttd_hover_evidence_v1.py", "openttd_contact_sheet_v1.py",
        "openttd_target_rebase_v1.py", "probe_openttd_target_rebase_v1.py",
        "hover_target_contract_v1.py", "hover_target_contract_schema_v1.json",
        "hover_target_reference_responder_v1.txt", "target_handle_model_runner_v2.py",
        "point_target_contract_v2.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py",
        "received_exchange_v2.py", "results/openttd-hover-target-pair-01/audit.json",
        "results/timing-envelope-openttd-matched-02/fixed-luna/runtime/020.png",
        "results/timing-envelope-openttd-matched-02/fixed-luna/runtime/004.png",
        "results/timing-envelope-openttd-matched-05/fixed-astra/runtime/012.png",
    ]
    task = [
        "openttd_task/interactive_l_hover_target_v1.py",
        "openttd_task/interactive_l_target_guard_v2.py",
        "openttd_task/guarded_l_score_v1.py",
        "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut",
        "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/baseline.sav",
    ]
    plan = {
        "status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-hover-rebased-pair-01", "seed": 991004,
        "execution_order": [
            {"name": "rehover-negative", "rehover_negative": True, "seed": 991004},
            {"name": "stable", "rehover_negative": False, "seed": 991004},
        ],
        "task": "hover-ground Road Construction, rebase identity, build guarded L",
        "fixed_hover": (
            "subsidies[432,51], trains[650,51], roads[820,51] in that order; "
            "800ms dwell plus immediate persistence observation per candidate"),
        "rebase": (
            "after one Luna-low hover-label decision, move pointer to neutral[1000,180], "
            "dwell800ms and observe; require exact24x14 target patch equality with the "
            "retained pre-hover source under unchanged binding; mint from pre-hover source"),
        "rehover_negative": (
            "after clean mint, hover roads[820,51] for800ms and confirm readable persistent "
            "Build roads evidence; observe_target_handle must return MISSING before target click"),
        "stable": (
            "after clean mint, request surface move[20,8], follow observed actual delta, "
            "complete local first-segment condition and all independent guarded L checks"),
        "promotion": (
            "hover and rebase readiness2/2; exact roads model contract2/2; rehover negative "
            "MISSING with zero target click; stable moved handle/local condition/engine pass"),
        "failure_policy": (
            "retain both first sessions; no retry or target/template/candidate/order/dwell/"
            "neutral-point/prompt/frame/region repair"),
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": (
            "two fresh same-save seed991004 OpenTTD X11 sessions and two Luna-low calls; "
            "three development-known candidates, fixed neutral point and one scripted "
            "guarded L; independent engine score; no automatic candidate/neutral discovery, "
            "unseen target, causal speed, cost, broad token or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
