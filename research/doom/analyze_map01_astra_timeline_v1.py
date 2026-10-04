"""Reconstruct the retained Astra attempt timeline from immutable telemetry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report_path = ROOT / "report.json"
    events_path = ROOT / "events.jsonl"
    report = json.loads(report_path.read_text())
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    decisions = report["decisions"]
    model_origin = min(d["controller_model_started_ns"] for d in decisions)

    rows = []
    for i, decision in enumerate(decisions):
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        next_start = decisions[i + 1]["controller_model_started_ns"] if i + 1 < len(decisions) else report["score"]["emit_ns"]
        d0, d1 = start - model_origin, next_start - model_origin
        interval_events = [e for e in events if start <= e.get("emit_ns", -1) < next_start]
        admissions = [e for e in interval_events if e["event"] == "input_admission"]
        held = [e for e in interval_events if e["event"] == "keys_held"]
        released = [e for e in interval_events if e["event"] == "terminal" and e.get("release", {}).get("verified")]
        observation_count = sum(e["event"] == "observation" for e in interval_events)
        a = decision["action"]
        rows.append({
            "iteration": i,
            "interval_start_s": round(d0 / 1e9, 3),
            "next_decision_or_score_s": round(d1 / 1e9, 3),
            "model_latency_s": round((end - start) / 1e9, 3),
            "health": [report["decisions"][i]["effect_memory"], None],
            "assessment": a["assessment"],
            "planned_commands": a["commands"],
            "contingencies_authored": len(a.get("contingencies", [])),
            "contingency_taken": decision.get("contingency_branch") is not None,
            "keys_held": [{"id": e.get("id"), "step": e.get("step"), "keys": e["keys"], "ack_s": round((e["input_ack_ns"] - model_origin) / 1e9, 3)} for e in held],
            "input_admission_count": len(admissions),
            "observation_count": observation_count,
            "verified_release_count": len(released),
            "effect_receipts": [{"action": r["action"], "result": r["result"], "samples": r["samples"]} for r in decision.get("effect_receipts", [])],
            "health_at_decision": None,
            "ammo_at_decision": None,
            "armor_at_decision": None,
        })
    # These values were manually transcribed from exact, hash-checked decision frames
    # by the existing failure analysis. They are deliberately joined by decision index.
    prior = json.loads((ROOT / "failure-analysis-v1.json").read_text())
    visual = prior["visual_transcription"]
    for row, health, ammo, armor in zip(rows, visual["health"], visual["ammo"], visual["armor"]):
        row["health_at_decision"], row["ammo_at_decision"], row["armor_at_decision"] = health, ammo, armor
        row.pop("health")
    out = {
        "schema": "agent-interface-map01-astra-timeline-v1",
        "source_run": "map01-astra-attempt-v1",
        "scope": "posthoc telemetry reconstruction; no new game run and no causal attribution",
        "time_origin": "monotonic nanoseconds as recorded in both report and event stream; interval endpoints use controller model start and next model start",
        "source_sha256": {"report.json": sha(report_path), "events.jsonl": sha(events_path), "failure-analysis-v1.json": sha(ROOT / "failure-analysis-v1.json")},
        "decision_interval_convention": "each row starts at its controller model start and ends at the next decision model start; final row ends at post-control score emission",
        "limitations": ["HUD values are existing manual transcription from exact decision frames, not per-observation readings", "visible threat presence is represented only by the model's recorded assessment; this is not independent detection", "input admissions and viewport effect receipts do not establish damage causality or task success"],
        "decisions": rows,
    }
    (ROOT / "timeline-v1.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "observations": sum(r["observation_count"] for r in rows), "input_admissions": sum(r["input_admission_count"] for r in rows), "verified_releases": sum(r["verified_release_count"] for r in rows), "output": str(ROOT / 'timeline-v1.json')}, indent=2))


if __name__ == "__main__":
    main()
