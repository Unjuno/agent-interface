"""Audit the retained alias failure and corrected common-client mechanics."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def main():
    failed = ROOT / "integrated-efficiency-three-arm-mechanics-01"
    plain_history = rows(failed / "plain" / "runtime" / "submission-history.jsonl")
    assert len(plain_history) == 6 and all(row["exact"] for row in plain_history)
    ephemeral_events = rows(failed / "ephemeral" / "runtime" / "events.jsonl")
    assert any(row.get("event") == "terminal" and row.get("error") ==
               "ValueError('target alias must match [a-z][a-z0-9_]{0,31}')"
               for row in ephemeral_events)
    assert not (failed / "persistent").exists()
    fixed = ROOT / "integrated-efficiency-three-arm-mechanics-02"
    report = json.loads((fixed / "report.json").read_text(encoding="utf-8"))
    assert report["passed"] is True and report["model_calls"] == 0
    expected = {"plain": (0, 12, 18, 36), "ephemeral": (12, 12, 48, 96),
                "persistent": (4, 12, 41, 82)}
    for arm, (mints, buttons, programs, calls) in expected.items():
        row = report["arms"][arm]
        assert (row["mints"], row["button_down"], row["programs"],
                row["durable_calls"]) == (mints, buttons, programs, calls)
        oracle = row["evaluation"]
        assert oracle["success"] is True and oracle["record_count"] == 6
        assert oracle["unexpected"] == [] and oracle["duplicates"] == {} and oracle["missing"] == []
        events = rows(fixed / arm / "runtime" / "events.jsonl")
        assert sum(event.get("event") == "pointer_admission" and
                   event.get("operation") == "button_down" for event in events) == 12
        terminals = [event for event in events if event.get("event") == "terminal"]
        assert len(terminals) == programs
        assert all(event["status"] == "completed" and event["release"]["verified"] is True
                   and event["release"]["keys_down"] == []
                   and event["release"]["buttons_down"] == [] for event in terminals)
    assert report["arms"]["persistent"]["invalidation"] == {
        "status": "MISSING", "eligible": False, "pointer_admissions": 0}
    print(json.dumps({"passed": True, "retained_alias_failure": True,
                      "fixed_exact_tasks": 18, "model_calls": 0,
                      "button_down_admissions": 36}, indent=2))

if __name__ == "__main__":
    main()
