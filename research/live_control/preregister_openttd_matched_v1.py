"""Freeze the matched OpenTTD comparison before any arm is executed."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/timing-envelope-openttd-matched-01"
SOURCES = [
    "preregister_openttd_matched_v1.py",
    "timing_envelope_openttd_matched_driver_v1.py",
    "timing_envelope_openttd_matched_supervisor_v1.py",
    "timing_envelope_v1.py",
    "timing_envelope_v2.py",
    "openttd_proposal_schema_v5.py",
    "model_pair_runner_v2.py",
    "pointer_socket_entry_v5.py",
    "session_v22.py",
    "openttd_contact_sheet_v1.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    "study": "timing-envelope-openttd-matched-01",
    "status": "PREREGISTERED_BEFORE_EXECUTION",
    "execution_order": ["fixed-luna", "fixed-astra", "adaptive"],
    "task_allocation": {
        "save": "fresh copy of the same canonical OpenTTD save for every arm",
        "seed_semantics": "canonical save; no RNG override",
        "task": "the ready event supplies the same guarded three-tile A-to-C road task",
        "max_model_turns": 9,
        "proposal_schema": "openttd_proposal_schema_v5.py",
        "independent_evaluator": "OpenTTD engine guard in the shared session runtime",
    },
    "arms": {
        "fixed-luna": "all turns gpt-5.6-luna low",
        "fixed-astra": "all turns gpt-6-astra medium",
        "adaptive": "turns 1-2 gpt-5.6-luna low, then gpt-6-astra medium",
    },
    "hard_success_gate": (
        "model requests verify with road_visible=true and the independent engine "
        "evaluation reports success=true within nine model turns"
    ),
    "primary_measurements": [
        "hard task success",
        "initial observation to semantic completion",
        "wrapper-observed model wait",
        "proposal publication to first useful feedback",
        "model calls and requested route",
        "reported model input/output/reasoning tokens",
        "durable calls, runtime frames, and contact sheets",
    ],
    "failure_policy": "retain the bounded independent failure score and do not retry an arm",
    "interpretation_limit": (
        "one fixed-order episode per arm is descriptive matched evidence, not a "
        "latency distribution, randomized causal estimate, or human comparison"
    ),
    "sources": {name: sha256(HERE / name) for name in SOURCES},
}
target = ROOT / "preregistration.json"
temporary = target.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, target)
print(target)
