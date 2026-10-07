"""Freeze the changed-initial-UI OpenTTD generalization probe before execution."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/timing-envelope-openttd-matched-04"
SOURCES = [
    "preregister_openttd_initial_state_v4.py",
    "timing_envelope_openttd_matched_driver_v4.py",
    "timing_envelope_openttd_matched_supervisor_v4.py",
    "timing_envelope_v1.py",
    "timing_envelope_v2.py",
    "openttd_proposal_schema_v5.py",
    "openttd_finish_outcome_v1.py",
    "model_pair_runner_v2.py",
    "pointer_socket_entry_v6.py",
    "session_v22.py",
    "openttd_contact_sheet_v1.py",
]
TASK_SOURCES = [
    "openttd_task/interactive_v7.py",
    "openttd_task/guarded_score.py",
    "openttd_task/observer_v2/common.nut",
    "openttd_task/observer_v2/main.nut",
    "openttd_task/observer_v2/info.nut",
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    "study": "timing-envelope-openttd-matched-04",
    "status": "PREREGISTERED_BEFORE_EXECUTION",
    "execution_order": ["fixed-astra-preopened-road-toolbar"],
    "task_allocation": {
        "save": "fresh copy of the same canonical OpenTTD save",
        "task_and_evaluator": "unchanged guarded three-tile A-to-C road task and independent engine score",
        "changed_factor": "road construction toolbar is opened by one setup click before the timed initial observation",
        "setup_exclusion": "the setup click is outside task actions and must be recorded with a negative initial engine score",
        "max_model_turns": 9,
    },
    "model_route": "all turns gpt-6-astra medium",
    "hard_success_gate": "model verify with road_visible=true plus independent evaluator success=true",
    "primary_measurements": [
        "hard task success",
        "initial observation to semantic completion",
        "wrapper-observed model wait",
        "proposal publication to first useful feedback",
        "model calls and reported model tokens",
        "durable calls, exact runtime frames, and contact sheets",
    ],
    "failure_policy": "retain typed independent failure or bounded failure; no retry",
    "decision_rule": (
        "This one episode tests adaptation to a preregistered changed initial UI state. "
        "Even on success it cannot promote a general route, establish a speedup, or replace a human baseline."
    ),
    "comparison_limit": (
        "The prior closed-toolbar episodes are contextual only because the initial visual state differs; "
        "model sampling and cache are uncontrolled."
    ),
    "sources": {
        **{name: digest(HERE / name) for name in SOURCES},
        **{name: digest(HERE.parent / name) for name in TASK_SOURCES},
    },
}
target = ROOT / "preregistration.json"
temporary = target.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, target)
print(target)



