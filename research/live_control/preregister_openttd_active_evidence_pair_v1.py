"""Freeze the model-proposed active-evidence OpenTTD pair before execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-active-evidence-pair-01"
LIVE_SOURCES = [
    "preregister_openttd_active_evidence_pair_v1.py",
    "run_openttd_active_evidence_pair_v1.py",
    "target_handle_model_runner_v2.py",
    "uncertain_target_contract_schema_v1.json",
    "uncertain_target_contract_v1.py",
    "uncertain_target_reference_responder_v1.txt",
    "openttd_hover_receipt_v1.py",
    "openttd_contact_sheet_v1.py",
    "evidence_target_contract_schema_v1.json",
    "evidence_target_contract_v1.py",
    "evidence_target_reference_responder_v1.txt",
    "openttd_finance_oracle_v1.py",
    "pointer_socket_entry_v19.py",
    "event_socket_v11.py",
    "session_v34.py", "session_v33.py", "model_point_target_v1.py",
    "session_v32.py", "observe_target_handle_v1.py", "session_v31.py",
    "session_v30.py", "session_v29.py", "session_v28.py", "session_v26.py",
    "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
    "local_target_guard_postcondition_v1.py", "session_v25.py", "session_v24.py",
    "local_displacement_postcondition_v1.py", "visual_anchor.py", "executor_v4.py",
    "point_target_contract_v2.py", "durable_submit_v4.py",
    "append_checkpoint_v1.py", "received_continuation_v1.py",
    "received_exchange_v2.py",
]
TASK_SOURCES = [
    "openttd_task/interactive_l_hover_target_v1.py",
    "openttd_task/interactive_l_target_guard_v2.py",
    "openttd_task/guarded_l_score_v1.py",
    "openttd_task/observer_l_v1/common.nut",
    "openttd_task/observer_l_v1/main.nut",
    "openttd_task/observer_l_v1/info.nut",
    "openttd_task/results/l-geometry-02/baseline.sav",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    plan = {
        "study": "openttd-active-evidence-pair-01",
        "execution_order": [
            {"name": "association-fault", "association_fault": True, "seed": 991004},
            {"name": "stable", "association_fault": False, "seed": 991004},
        ],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "low",
        "task": "open the company finances window",
        "policy": (
            "one model proposes exactly three candidates; candidates grant no authority; "
            "runtime collects persistent hover receipts; a second call to the same model may "
            "select only a receipt-bound point; selected evidence is rehovered before ordinary "
            "input admission; no model retry"),
        "negative": (
            "reverse the verifier's candidate association while retaining the executed hover "
            "program; generic receipt verification must refuse before the evidence-selection "
            "model call and before target input"),
        "positive": (
            "use the model-authored candidate order, require persistent evidence, select through "
            "the same model, rehover exact evidence, click through ordinary admission, and require "
            "the independent fixed-seed exact-title oracle"),
        "scope": (
            "two fresh same-seed X11 cases and one toolbar task; candidate positions are authored "
            "by the model with no answer coordinate in the runner; this does not establish broad "
            "unknown-GUI grounding, latency improvement, token reduction, or human tempo"),
        "sources": {
            **{name: sha(HERE / name) for name in LIVE_SOURCES},
            **{name: sha(HERE.parent / name) for name in TASK_SOURCES},
        },
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
