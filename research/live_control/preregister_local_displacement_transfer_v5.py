"""Freeze an unchanged opposite-order replication using canonical JSON identity."""
import hashlib
import json
from pathlib import Path

from parse_local_displacement_author_v1 import parse


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-displacement-transfer-05"
AUTHOR_REL = Path("results/local-displacement-authorship-01/luna-1/events.jsonl")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    wire = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(wire).hexdigest()


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
    prior = json.loads((HERE / "results/local-displacement-transfer-03/authored-postcondition.json").read_text())
    assert spec == prior
    (OUT / "authored-postcondition.json").write_text(json.dumps(spec, indent=2) + "\n")
    sources = [
        "preregister_local_displacement_transfer_v5.py",
        "run_local_displacement_transfer_v5.py", "run_local_displacement_transfer_v4.py",
        "parse_local_displacement_author_v1.py", "session_v24.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py",
        "session_v23.py", "local_visual_barrier_program_v1.py", "local_visual_barrier_v1.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
    ]
    plan = {
        "status": "preregistered_before_fresh_x11_execution",
        "correction": "v4 failed before preregistration or input because byte identity was line-ending sensitive; v5 binds canonical parsed JSON identity",
        "replicates": "local-displacement-transfer-03 with unchanged authored condition and allocations",
        "order_change": "v3 target-to-partial; v5 partial-to-target to expose order/focus sensitivity",
        "order": ["partial", "target"], "seed": 991003,
        "authored_source_relative": str(AUTHOR_REL).replace("\\", "/"),
        "authored_source_sha256": sha(HERE / AUTHOR_REL),
        "authored_output": spec,
        "authored_output_canonical_sha256": canonical_sha(spec),
        "prior_authored_output_canonical_sha256": canonical_sha(prior),
        "allocations": {"target": {"pointer_delta": 28, "expected_visual_delta": [24, 0],
                                   "expected_postcondition": "met", "save": True},
                        "partial": {"pointer_delta": 24, "expected_visual_delta": [20, 0],
                                    "expected_postcondition": "target_not_reached", "save": False}},
        "primary_endpoint": "unchanged replication: fresh 24px target starts Save and fresh 20px partial stops before Save",
        "failure_policy": "retain first result of each ordered allocation; no retry or replacement; early terminal is a typed failed case",
        "interpretation": "second fresh same-task pair for the unchanged first Luna-authored patch; scripted pointer paths; no live model call, speed, token, cross-domain or generalization claim",
        "sources": {name: sha(HERE / name) for name in sources},
    }
    assert plan["authored_output_canonical_sha256"] == plan["prior_authored_output_canonical_sha256"]
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
