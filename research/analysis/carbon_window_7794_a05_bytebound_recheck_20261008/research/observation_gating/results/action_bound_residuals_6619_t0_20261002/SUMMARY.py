from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main():
    raw = json.loads((HERE / "formal_01" / "candidate_output" / "raw.json").read_text())
    oracle = json.loads((HERE / "fixture" / "oracle.json").read_text())
    events = {row["case_id"]: row["events"] for row in oracle["cases"]}
    non_events = [case_id for case_id, ledger in events.items() if not ledger]
    methods = ("raw_delta", "global_registration", "action_bound", "sham_bound")
    scores = {}
    for method in methods:
        detections = 0
        event_count = 0
        for row in raw["rows"]:
            for event in events[row["case_id"]]:
                event_count += 1
                if (event["onset_ns"] <= row["capture_ns"] <= event["deadline_ns"] and
                        row["methods"][method]["alarm"]):
                    detections += 1
        false_alarms = sum(bool(next(row for row in raw["rows"]
                                     if row["case_id"] == case_id)["methods"][method]["alarm"])
                           for case_id in non_events)
        scores[method] = {"deadline_detections": detections,
                          "scheduled_events": event_count,
                          "false_alarm_cases": false_alarms,
                          "non_event_cases": len(non_events)}
    summary = {"schema": "action-bound-residual-supplemental-summary-v1",
               "candidate_raw_sha256": __import__("hashlib").sha256(
                   (HERE / "formal_01" / "candidate_output" / "raw.json").read_bytes()).hexdigest(),
               "denominator": {"cases": len(raw["rows"]), "events": 5,
                               "non_event_cases": len(non_events)},
               "methods": scores,
               "note": "Posthoc counts from immutable formal raw/oracle; does not rerun candidate or auditor."}
    out = HERE / "SUPPLEMENTAL_SUMMARY.json"
    out.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
