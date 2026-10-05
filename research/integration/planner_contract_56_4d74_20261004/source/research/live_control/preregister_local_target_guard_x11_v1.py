"""Freeze a fresh X11 target, partial and guard integration allocation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-target-guard-x11-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    sources = [
        "preregister_local_target_guard_x11_v1.py", "run_local_target_guard_x11_v1.py",
        "session_v25.py", "local_target_guard_postcondition_v1.py",
        "session_v24.py", "local_displacement_postcondition_v1.py", "visual_anchor.py",
        "session_v23.py", "local_visual_barrier_program_v1.py", "local_visual_barrier_v1.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
    ]
    condition = {
        "op": "local_target_guard_postcondition", "postcondition_id": "red-placement-right-24",
        "source_sequence": 1, "target_boxes": [[664, 376, 3, 28]],
        "guard_boxes": [[600, 354, 30, 15]], "pixel_delta_threshold": 24,
        "minimum_target_changed_pixels": 50, "maximum_guard_changed_pixels": 20,
        "required_samples": 2, "sample_interval_ms": 50, "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }
    plan = {
        "status": "preregistered_before_fresh_x11_execution",
        "order": ["target", "partial", "guard"], "seed": 991003,
        "condition": condition,
        "allocations": {
            "target": {"pointer_delta": [28, 0], "expected_visual_delta": [24, 0],
                       "expected_reason": "met", "save": True},
            "partial": {"pointer_delta": [24, 0], "expected_visual_delta": [20, 0],
                        "expected_reason": "target_not_reached", "save": False},
            "guard": {"pointer_delta": [0, -24], "expected_visual_delta": [0, -20],
                      "expected_reason": "guard_changed", "save": False},
        },
        "primary_endpoint": "only target24px starts Save; partial20px and upward guard intrusion stop before Save",
        "failure_policy": "retain first result of every ordered allocation; no retry; early terminal is typed failure",
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "fresh scripted Inkscape integration of the target/guard operator; no model call, OpenTTD live transfer, semantic success, speed or generalization claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
