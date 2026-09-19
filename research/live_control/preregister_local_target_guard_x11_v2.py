"""Freeze a reversed-order target/guard allocation after a safe focus interruption."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-target-guard-x11-02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    previous = json.loads((HERE / "results/local-target-guard-x11-01/preregistration.json").read_text())
    sources = ["preregister_local_target_guard_x11_v2.py", "run_local_target_guard_x11_v2.py",
               "run_local_target_guard_x11_v1.py", "session_v25.py",
               "local_target_guard_postcondition_v1.py", "session_v24.py",
               "local_displacement_postcondition_v1.py", "visual_anchor.py",
               "session_v23.py", "local_visual_barrier_program_v1.py",
               "local_visual_barrier_v1.py", "session_v22.py", "session_v21.py",
               "session_v20.py", "session_v19.py", "session_v18.py", "session_v17.py",
               "session_v16.py", "session_v15.py", "session_v14.py", "session_v13.py",
               "session_v12.py", "session_v11.py", "session_v10.py", "session_v9.py",
               "executor_v3.py", "lease.py"]
    plan = {
        "status": "preregistered_before_fresh_x11_execution",
        "correction": "v1 target was safely interrupted by focus_changed immediately after button-down; partial and guard passed; v2 reverses order and preserves all three new allocations",
        "order": ["guard", "partial", "target"], "seed": previous["seed"],
        "condition": previous["condition"], "allocations": previous["allocations"],
        "primary_endpoint": previous["primary_endpoint"],
        "failure_policy": previous["failure_policy"],
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": previous["scope"],
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
