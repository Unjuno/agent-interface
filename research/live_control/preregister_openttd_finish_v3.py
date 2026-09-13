"""Freeze the fresh v3 negative and positive finish-path validation."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/timing-envelope-openttd-matched-03"
SOURCES = [
    "preregister_openttd_finish_v3.py",
    "openttd_negative_finish_live_v1.py",
    "openttd_finish_outcome_v1.py",
    "timing_envelope_openttd_matched_driver_v3.py",
    "timing_envelope_openttd_matched_supervisor_v3.py",
    "timing_envelope_v1.py",
    "timing_envelope_v2.py",
    "openttd_proposal_schema_v5.py",
    "model_pair_runner_v2.py",
    "pointer_socket_entry_v5.py",
    "session_v22.py",
    "openttd_contact_sheet_v1.py",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    "study": "timing-envelope-openttd-matched-03",
    "status": "PREREGISTERED_BEFORE_EXECUTION",
    "execution_order": ["negative-control", "fixed-astra"],
    "negative_control": {
        "model_calls": 0,
        "task_input_calls": 0,
        "expected_engine_success": False,
        "expected_failure_mode": "visual_verify_false_positive",
    },
    "positive_path": {
        "model_route": "all turns gpt-6-astra medium",
        "max_model_turns": 9,
        "hard_success_gate": "model verify plus independent evaluator success",
    },
    "shared": "fresh copies of the same canonical OpenTTD save and independent evaluator",
    "interpretation_limit": "finish-path live integration plus one additional fixed-Astra episode; no population estimate or human comparison",
    "sources": {name: digest(HERE / name) for name in SOURCES},
}
target = ROOT / "preregistration.json"
temporary = target.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, target)
print(target)
