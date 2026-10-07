"""Audit retained schema failures and successful controlled-context v4 screen."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failure_messages = {
        "target-handle-model-screen-02": "schema must have a 'type' key",
        "target-handle-model-screen-03": "schema must be a JSON Schema of 'type:",
    }
    failures = {}
    for study, expected in failure_messages.items():
        root = HERE / "results" / study
        events = [
            json.loads(line)
            for line in (root / "call-1-coordinate/events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        errors = [row["message"] for row in events if row.get("type") == "error"]
        assert len(errors) == 1 and expected in errors[0]
        assert not [row for row in events if row.get("type") == "turn.completed"]
        failures[study] = {
            "server_rejected_before_completed_turn": True,
            "error_contains": expected,
        }
    root = HERE / "results/target-handle-model-screen-04"
    plan = read(root / "plan.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(root / "report.json")
    assert report["promotion_gate"]["passed"] is True
    assert [row["mode"] for row in report["results"]] == plan["order"]
    assert all(row["correct"] for row in report["results"])
    assert report["arms"]["coordinate"]["reported"] == [9268, 9268]
    assert report["arms"]["handle"]["reported"] == [8009, 8009]
    audit = {
        "audit_passed": True,
        "pre_model_schema_failures": failures,
        "v4": {
            "correct": "4/4",
            "coordinate_input_mean": 9268,
            "handle_input_mean": 8009,
            "handle_minus_coordinate": -1259,
            "handle_reduction_percent": (9268 - 8009) / 9268 * 100,
            "within_arm_ranges": {
                "coordinate": report["arms"]["coordinate"]["reported_range"],
                "handle": report["arms"]["handle"]["reported_range"],
            },
            "promotion_gate_passed": True,
        },
        "scope": plan["scope"],
    }
    (root / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
