"""Independent consistency checks for the retained MAP01 timeline reconstruction."""
import hashlib
import json
import copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(timeline, report, events, visual):
    assert timeline["schema"] == "agent-interface-map01-astra-timeline-v1"
    rows = timeline["decisions"]
    assert len(rows) == len(report["decisions"]) == 13
    assert [row["iteration"] for row in rows] == list(range(13))
    assert all(a["interval_start_s"] < a["next_decision_or_score_s"] for a in rows)
    assert all(rows[i]["next_decision_or_score_s"] == rows[i + 1]["interval_start_s"] for i in range(12))
    raw_counts = {kind: sum(event["event"] == kind for event in events) for kind in ("observation", "input_admission", "terminal")}
    assert raw_counts == {"observation": 530, "input_admission": 46, "terminal": 26}
    model_origin = min(d["controller_model_started_ns"] for d in report["decisions"])
    for i, (row, decision) in enumerate(zip(rows, report["decisions"])):
        start = decision["controller_model_started_ns"]
        stop = report["decisions"][i + 1]["controller_model_started_ns"] if i + 1 < len(rows) else report["score"]["emit_ns"]
        span = [e for e in events if start <= e.get("emit_ns", -1) < stop]
        expected_holds = [
            {"id": e.get("id"), "step": e.get("step"), "keys": e["keys"], "ack_s": round((e["input_ack_ns"] - model_origin) / 1e9, 3)}
            for e in span if e["event"] == "keys_held"
        ]
        expected_releases = sum(e["event"] == "terminal" and e.get("release", {}).get("verified") is True for e in span)
        assert row["interval_start_s"] == round((start - model_origin) / 1e9, 3)
        assert row["next_decision_or_score_s"] == round((stop - model_origin) / 1e9, 3)
        assert row["model_latency_s"] == round((decision["controller_model_ended_ns"] - start) / 1e9, 3)
        assert row["assessment"] == decision["action"]["assessment"]
        assert row["planned_commands"] == decision["action"]["commands"]
        assert row["contingencies_authored"] == len(decision["action"].get("contingencies", []))
        assert row["contingency_taken"] is (decision.get("contingency_branch") is not None)
        assert row["keys_held"] == expected_holds
        assert row["input_admission_count"] == sum(e["event"] == "input_admission" for e in span)
        assert row["observation_count"] == sum(e["event"] == "observation" for e in span)
        assert row["verified_release_count"] == expected_releases
        assert row["effect_receipts"] == [{"action": r["action"], "result": r["result"], "samples": r["samples"]} for r in decision.get("effect_receipts", [])]
        assert row["health_at_decision"] == visual["health"][i]
        assert row["ammo_at_decision"] == visual["ammo"][i]
        assert row["armor_at_decision"] == visual["armor"][i]
    assert sum(row["observation_count"] for row in rows) == 528
    assert sum(row["input_admission_count"] for row in rows) == 46
    assert sum(row["verified_release_count"] for row in rows) == 26
    assert sum(row["contingencies_authored"] for row in rows) == 8
    assert not any(row["contingency_taken"] for row in rows)
    assert report["score"]["map_exit"] is False and report["score"]["player_dead"] is True


def load_inputs():
    timeline = json.loads((ROOT / "timeline-v1.json").read_text())
    report = json.loads((ROOT / "report.json").read_text())
    events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
    failure = json.loads((ROOT / "failure-analysis-v1.json").read_text())
    assert timeline["source_sha256"]["report.json"] == digest(ROOT / "report.json")
    assert timeline["source_sha256"]["events.jsonl"] == digest(ROOT / "events.jsonl")
    assert timeline["source_sha256"]["failure-analysis-v1.json"] == digest(ROOT / "failure-analysis-v1.json")
    return timeline, report, events, failure["visual_transcription"]


def main():
    timeline, report, events, visual = load_inputs()
    audit(timeline, report, events, visual)
    print(json.dumps({"passed": True, "decision_intervals": 13, "interval_observations": 528, "raw_observations": 530, "input_admissions": 46, "verified_releases": 26, "contingencies_taken": 0}, indent=2))


if __name__ == "__main__":
    main()
