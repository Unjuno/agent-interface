"""Audit five retained persistent-mechanics engineering allocations."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"

def records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def events(index):
    return records(ROOT / f"integrated-efficiency-persistent-mechanics-{index:02d}" / "runtime" / "events.jsonl")

def history(index):
    path = ROOT / f"integrated-efficiency-persistent-mechanics-{index:02d}" / "runtime" / "submission-history.jsonl"
    return [] if not path.exists() else records(path)

def main():
    assert any(row.get("event") == "terminal" and row.get("error") ==
               "ValueError('visually flat target region refused')" for row in events(1))
    assert history(1) == []
    assert len(history(2)) == 3 and all(row["exact"] for row in history(2))
    assert any(row.get("event") == "target_handle_checked" and row.get("status") == "MISSING"
               and row.get("handle") == "field_a" for row in events(2))
    assert len(history(3)) == 3 and all(row["exact"] for row in history(3))
    assert any(row.get("event") == "terminal" and row.get("error") ==
               "ValueError('visually flat target region refused')" for row in events(3))
    fourth = json.loads((ROOT / "integrated-efficiency-persistent-mechanics-04" /
                         "report.json").read_text(encoding="utf-8"))
    fourth_events = events(4)
    assert fourth["passed"] is True and fourth["independent_evaluation"]["success"] is True
    assert sum(row.get("event") == "pointer_admission" and row.get("operation") == "button_down"
               for row in fourth_events) == 12
    assert sum(len(row["pointer_admissions"]) for row in fourth["programs"]) == 0
    fifth = json.loads((ROOT / "integrated-efficiency-persistent-mechanics-05" /
                        "report.json").read_text(encoding="utf-8"))
    fifth_events = events(5)
    assert fifth["passed"] is True and fifth["tasks_completed"] == 6
    assert fifth["model_calls"] == 0 and fifth["target_button_down_admissions"] == 12
    assert fifth["old_target_pointer_admissions"] == 0
    assert fifth["invalidation"] == {"status": "MISSING", "eligible": False, "sequence": None}
    oracle = fifth["independent_evaluation"]
    assert oracle["success"] is True and oracle["record_count"] == 6
    assert oracle["unexpected"] == [] and oracle["duplicates"] == {} and oracle["missing"] == []
    assert all(value == 1 for value in oracle["exact_counts"].values())
    old = next(row for row in fifth["programs"] if row["label"] == "old-field-invalidation")
    assert old["pointer_admissions"] == []
    target = [row for row in fifth["programs"] if row["label"].startswith(("enter-", "submit-"))]
    assert len(target) == 12
    assert all(sum(event["operation"] == "button_down" for event in row["pointer_admissions"]) == 1
               for row in target)
    terminals = [row for row in fifth_events if row.get("event") == "terminal"]
    assert len(terminals) == 41
    assert all(row["release"]["verified"] is True and row["release"]["keys_down"] == []
               and row["release"]["buttons_down"] == [] for row in terminals)
    print(json.dumps({"passed": True, "retained_allocations": 5,
                      "final_exact_tasks": 6, "target_button_down_admissions": 12,
                      "old_target_button_down_admissions": 0}, indent=2))

if __name__ == "__main__":
    main()
