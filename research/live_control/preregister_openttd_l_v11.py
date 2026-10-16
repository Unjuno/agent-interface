"""Freeze the first changed-geometry L effect-memory allocation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/timing-envelope-openttd-l-11"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    live_names = [
        "timing_envelope_openttd_l_supervisor_v11.py",
        "timing_envelope_openttd_l_supervisor_v9.py",
        "timing_envelope_openttd_l_supervisor_v8.py",
        "timing_envelope_openttd_l_driver_v7.py",
        "timing_envelope_openttd_l_driver_v6.py",
        "pointer_socket_entry_v9.py",
        "openttd_effect_memory_v1.py",
        "semantic_checkpoint_v4.py",
        "openttd_finish_outcome_v2.py",
        "model_pair_runner_v2.py",
        "session_v22.py",
    ]
    task_names = [
        "openttd_task/interactive_l_v2.py",
        "openttd_task/interactive_l_v1.py",
        "openttd_task/guarded_l_score_v1.py",
        "openttd_task/observer_l_v1/common.nut",
        "openttd_task/observer_l_v1/main.nut",
        "openttd_task/observer_l_v1/info.nut",
        "openttd_task/results/l-geometry-02/manifest.json",
        "openttd_task/results/l-geometry-02/audit.json",
        "openttd_task/results/l-geometry-02/baseline.sav",
    ]
    prior = json.loads((HERE / "results/timing-envelope-openttd-l-10/audit.json").read_text())
    fixture = json.loads((HERE.parent / "openttd_task/results/l-geometry-02/audit.json").read_text())
    preregistration = {
        "status": "preregistered_before_execution",
        "study": "timing-envelope-openttd-l-11",
        "arm": "fixed-astra",
        "execution": "first and only model allocation; no retry or manual intervention",
        "task": {
            "seed": 991004,
            "save_sha256": fixture["save_sha256"],
            "target": fixture["contract"]["target"],
            "forbidden": fixture["contract"]["forbidden"],
            "same_semantics": "five-tile L from A through B to C; four X-square tiles clear",
            "changed_from_v9_v10": ["seed", "save bytes", "map origin", "target and guard tiles", "screen position"],
        },
        "model_route": "all gpt-6-astra medium; maximum 12 turns",
        "intervention": "unchanged one-unresolved-drag bounded effect memory from v9/v10",
        "primary_endpoint": "independent hard success or retained typed failure on first execution",
        "secondary_endpoints": [
            "checkpoint transition sequence and effect-memory replay",
            "distinct versus repeated completed-segment drags",
            "model turns and actual token usage",
            "model wait, proposal-to-feedback and semantic completion",
            "verified input release terminals",
        ],
        "prior_same_geometry": {
            "successes": 2,
            "episodes": 2,
            "turns": [9, 9],
            "semantic_completion_ms": [153026.5392, 160836.8125],
            "v10_audit_sha256": sha(HERE / "results/timing-envelope-openttd-l-10/audit.json"),
        },
        "decision_rule": "retain first outcome; changed-geometry success advances to another allocation but does not by itself promote",
        "sources": {
            **{name: sha(HERE / name) for name in live_names},
            **{name: sha(HERE.parent / name) for name in task_names},
        },
    }
    (OUT / "preregistration.json").write_text(json.dumps(preregistration, indent=2) + "\n")
    print(json.dumps(preregistration, indent=2))


if __name__ == "__main__":
    main()
