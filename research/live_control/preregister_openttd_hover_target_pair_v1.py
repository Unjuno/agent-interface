"""Freeze bounded hover-label grounding before fresh OpenTTD execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-hover-target-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    live = [
        "preregister_openttd_hover_target_pair_v1.py",
        "run_openttd_hover_target_pair_v1.py", "pointer_socket_entry_v19.py",
        "event_socket_v11.py", "session_v34.py", "session_v33.py",
        "model_point_target_v1.py", "session_v32.py", "observe_target_handle_v1.py",
        "session_v31.py", "session_v30.py", "session_v29.py", "session_v28.py",
        "session_v26.py", "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "local_target_guard_postcondition_v1.py", "session_v25.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py", "executor_v4.py",
        "openttd_hover_evidence_v1.py", "openttd_contact_sheet_v1.py",
        "hover_target_contract_v1.py", "hover_target_contract_schema_v1.json",
        "hover_target_reference_responder_v1.txt", "target_handle_model_runner_v2.py",
        "point_target_contract_v2.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py",
        "received_exchange_v2.py", "probe_openttd_hover_evidence_v1.py",
        "results/openttd-point-contract-pair-01/audit.json",
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
        "study": "openttd-hover-target-pair-01", "seed": 991004,
        "execution_order": [
            {"name": "association-fault", "association_fault": True, "seed": 991004},
            {"name": "stable", "association_fault": False, "seed": 991004},
        ],
        "task": "hover-ground Road Construction, then build the guarded five-tile L",
        "candidates": {
            "subsidies": [432, 51], "trains": [650, 51], "roads": [820, 51]},
        "candidate_basis": (
            "roads is the prior independently successful target; subsidies and trains "
            "are the exact two points selected by the failed direct-point pair"),
        "hover_program": (
            "fixed order subsidies,trains,roads; one pointer move, 800ms dwell capture "
            "and immediate persistence capture per candidate; 2400ms total declared dwell"),
        "readiness": (
            "same focus/surface/geometry for all evidence; exact admitted candidate points; "
            "each dwell and persistence frame must classify to its preregistered readable "
            "tooltip bitmap and exact candidate association before presentation"),
        "association_fault": (
            "after valid fresh hovers, swap subsidies/trains declaration; verifier must "
            "refuse before model delivery, target click or task mutation"),
        "stable": (
            "one Luna-low call receives current full frame plus three labeled hover strips; "
            "candidate-id/point contract must select roads [820,51]; mint fixed24x14 target, "
            "follow observed surface delta and complete independent guarded L score"),
        "baseline": (
            "retained direct full-frame pair semantic point grounding0/2; stable9296 input "
            "tokens and18628.776261ms decision-to-independent-evaluation, descriptive only"),
        "promotion": (
            "readiness2/2; association fault refused before model/target click; stable exact "
            "roads contract, moved handle, local condition met and all engine checks true"),
        "failure_policy": (
            "retain both first sessions; no retry or template/candidate/order/dwell/prompt/"
            "point/frame/size repair; readiness failure gets no model or target click"),
        "sources": {**{name: sha(HERE / name) for name in live},
                    **{name: sha(HERE.parent / name) for name in task}},
        "scope": (
            "two fresh same-save seed991004 OpenTTD X11 sessions, one Luna-low image call "
            "maximum, three development-known candidates and one scripted guarded L; "
            "independent engine score; no automatic candidate discovery, unseen target, "
            "causal speed, cost, broad token or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
