"""Freeze the new-geometry OpenTTD negative and fixed-Astra episodes."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/timing-envelope-openttd-matched-05"
SOURCES = [
    "preregister_openttd_geometry_v5.py",
    "openttd_negative_finish_geometry_v2.py",
    "openttd_finish_outcome_v1.py",
    "timing_envelope_openttd_matched_driver_v5.py",
    "timing_envelope_openttd_matched_supervisor_v5.py",
    "timing_envelope_v1.py",
    "timing_envelope_v2.py",
    "openttd_proposal_schema_v5.py",
    "model_pair_runner_v2.py",
    "pointer_socket_entry_v7.py",
    "session_v22.py",
    "openttd_contact_sheet_v1.py",
]
TASK_SOURCES = [
    "openttd_task/interactive_v8.py",
    "openttd_task/guarded_score_v2.py",
    "openttd_task/observer_v2/common.nut",
    "openttd_task/observer_v2/main.nut",
    "openttd_task/observer_v2/info.nut",
    "openttd_task/results/geometry-01/manifest.json",
    "openttd_task/results/geometry-01/audit.json",
    "openttd_task/results/geometry-01/baseline.sav",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    "study": "timing-envelope-openttd-matched-05",
    "status": "PREREGISTERED_BEFORE_EXECUTION",
    "execution_order": ["negative-control", "fixed-astra"],
    "task_allocation": {
        "seed": 991002,
        "save_sha256": "2cfdb42ee2f3d1b44e89920387a2299b44072801198cbc76ff88a7609c6c12f7",
        "target_tiles": [465, 466, 467],
        "forbidden_tiles": [529, 530, 531],
        "viewport": "saved around offset tile 663; target visibly shifted from prior geometry",
        "toolbar": "closed",
        "task": "same straight A-to-C road semantics on a new map and screen position",
        "max_model_turns": 9,
        "evaluator": "geometry-derived independent guarded_score_v2",
    },
    "negative_control": {
        "model_calls": 0,
        "task_input_calls": 0,
        "expected_engine_success": False,
        "expected_failure_mode": "visual_verify_false_positive",
    },
    "positive_path": {
        "model_route": "all turns gpt-6-astra medium",
        "hard_success_gate": "model verify plus independent evaluator success",
    },
    "primary_measurements": [
        "hard task success",
        "initial observation to semantic completion",
        "wrapper-observed model wait",
        "proposal publication to first useful feedback",
        "model calls and reported token usage",
        "durable calls, exact frames and contact sheets",
    ],
    "failure_policy": "retain the first bounded or typed independent failure and do not retry",
    "interpretation_limit": "one new-geometry episode; no general route, latency distribution, human comparison or speedup claim",
    "sources": {
        **{name: digest(HERE / name) for name in SOURCES},
        **{name: digest(HERE.parent / name) for name in TASK_SOURCES},
    },
}
path = ROOT / "preregistration.json"
temporary = path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
print(path)

