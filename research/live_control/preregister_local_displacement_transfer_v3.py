"""Freeze a robust reversed-order replication of the authored condition transfer."""
import hashlib
import json
from pathlib import Path

from parse_local_displacement_author_v1 import parse


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-displacement-transfer-03"
AUTHOR_REL = Path("results/local-displacement-authorship-01/luna-1/events.jsonl")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authored():
    rows = [json.loads(line) for line in (HERE / AUTHOR_REL).read_text().splitlines()]
    messages = [row["item"]["text"] for row in rows
                if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    if len(messages) != 1:
        raise ValueError("one frozen author message required")
    return parse(messages[0])


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    spec = authored()
    (OUT / "authored-postcondition.json").write_text(json.dumps(spec, indent=2) + "\n")
    sources = [
        "preregister_local_displacement_transfer_v3.py",
        "run_local_displacement_transfer_v3.py", "parse_local_displacement_author_v1.py",
        "session_v24.py", "local_displacement_postcondition_v1.py", "visual_anchor.py",
        "session_v23.py", "local_visual_barrier_program_v1.py", "local_visual_barrier_v1.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
    ]
    plan = {
        "status": "preregistered_before_fresh_x11_execution",
        "correction": "v2 partial passed, then target was safely interrupted by focus_changed; v2 packaging assumed the postcondition event always existed; v3 preserves any early terminal as data",
        "order": ["target", "partial"], "seed": 991003,
        "authored_source_relative": str(AUTHOR_REL).replace("\\", "/"),
        "authored_source_sha256": sha(HERE / AUTHOR_REL),
        "authored_output": spec, "authored_output_sha256": sha(OUT / "authored-postcondition.json"),
        "allocations": {"target": {"pointer_delta": 28, "expected_visual_delta": [24, 0],
                                   "expected_postcondition": "met", "save": True},
                        "partial": {"pointer_delta": 24, "expected_visual_delta": [20, 0],
                                    "expected_postcondition": "target_not_reached", "save": False}},
        "primary_endpoint": "fresh target reaches authored 24px condition and starts Save; fresh partial stops before Save",
        "failure_policy": "retain first result of each ordered allocation; no retry or replacement; early terminal is a typed failed case",
        "interpretation": "unchanged first Luna-authored patch transferred to fresh same-task X11 processes; scripted pointer paths; no live model call, speed, token, cross-domain or promotion claim",
        "sources": {name: sha(HERE / name) for name in sources},
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
