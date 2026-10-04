"""Independent consistency checks for the retained MAP01 timeline reconstruction."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    timeline = json.loads((ROOT / "timeline-v1.json").read_text())
    report = json.loads((ROOT / "report.json").read_text())
    events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
    assert timeline["schema"] == "agent-interface-map01-astra-timeline-v1"
    assert timeline["source_sha256"]["report.json"] == digest(ROOT / "report.json")
    assert timeline["source_sha256"]["events.jsonl"] == digest(ROOT / "events.jsonl")
    assert timeline["source_sha256"]["failure-analysis-v1.json"] == digest(ROOT / "failure-analysis-v1.json")
    rows = timeline["decisions"]
    assert len(rows) == len(report["decisions"]) == 13
    assert [row["iteration"] for row in rows] == list(range(13))
    assert all(a["interval_start_s"] < a["next_decision_or_score_s"] for a in rows)
    assert all(rows[i]["next_decision_or_score_s"] == rows[i + 1]["interval_start_s"] for i in range(12))
    assert sum(row["observation_count"] for row in rows) == 528
    assert sum(row["input_admission_count"] for row in rows) == 46
    assert sum(row["verified_release_count"] for row in rows) == 26
    assert sum(row["contingencies_authored"] for row in rows) == 8
    assert not any(row["contingency_taken"] for row in rows)
    raw_counts = {kind: sum(event["event"] == kind for event in events) for kind in ("observation", "input_admission", "terminal")}
    assert raw_counts == {"observation": 530, "input_admission": 46, "terminal": 26}
    assert report["score"]["map_exit"] is False and report["score"]["player_dead"] is True
    print(json.dumps({"passed": True, "decision_intervals": 13, "interval_observations": 528, "raw_observations": 530, "input_admissions": 46, "verified_releases": 26, "contingencies_taken": 0}, indent=2))


if __name__ == "__main__":
    main()
