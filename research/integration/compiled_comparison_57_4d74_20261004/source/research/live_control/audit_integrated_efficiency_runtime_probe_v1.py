"""Audit the retained URL failure and corrected A/B runtime probe."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    failed = RESULTS / "integrated-efficiency-runtime-probe-01" / "runtime"
    failed_events = rows(failed / "events.jsonl")
    rejected = [row for row in failed_events if row.get("event") == "rejected"]
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "unsupported text; reject entire program before input"
    assert not any(row.get("event") in {"button_down", "button_up"} for row in failed_events)
    assert not (failed / "submission-history.jsonl").exists()

    fixed = RESULTS / "integrated-efficiency-runtime-probe-02"
    report = json.loads((fixed / "report.json").read_text(encoding="utf-8"))
    assert report["passed"] is True and report["model_calls"] == 0
    assert report["task_inputs"] == 0
    assert [(row["task_id"], row["layout"]) for row in report["observations"]] == [
        ("task-1", "A"), ("task-4", "B")]
    assert len({row["image_sha256"] for row in report["observations"]}) == 2
    for row in report["observations"]:
        image = fixed / "runtime" / row["image"]
        assert image.exists()
        assert hashlib.sha256(image.read_bytes()).hexdigest() == row["image_sha256"]
    evaluation = report["independent_evaluation"]
    assert evaluation["success"] is False and evaluation["record_count"] == 0
    assert evaluation["missing"] == [f"task-{index}" for index in range(1, 7)]
    events = rows(fixed / "runtime" / "events.jsonl")
    terminals = [row for row in events if row.get("event") == "terminal"]
    assert len(terminals) == 4
    assert all(row["status"] == "completed" and row["release"]["verified"] is True
               and row["release"]["keys_down"] == []
               and row["release"]["buttons_down"] == [] for row in terminals)
    assert not (fixed / "runtime" / "submission-history.jsonl").exists()
    print(json.dumps({"passed": True, "retained_failure": "unsupported_query_url_text",
                      "corrected_layout_observations": 2, "task_inputs": 0}, indent=2))


if __name__ == "__main__":
    main()
