#!/usr/bin/env python3
"""Independent raw and summary audit for the A04 result."""
import argparse
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = next(p for p in PKG.parents if (p / ".git").exists())
SOURCE = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
PIN = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"


def independently_reconstruct(raw):
    events = [json.loads(line) for line in raw.splitlines()]
    admissions = [(i, e) for i, e in enumerate(events)
                  if e.get("event") == "input_admission"]
    holds = [(i, e) for i, e in enumerate(events)
             if e.get("event") == "keys_held"]
    by_key = {}
    for pos, receipt in holds:
        keys = receipt.get("keys")
        if type(keys) is list:
            for key in set(keys):
                by_key.setdefault(key, []).append((pos, receipt))

    rows = []
    for pos, admission in admissions:
        candidates = [(j, hold) for j, hold in by_key.get(admission.get("key"), ())
                      if j > pos]
        rows.append({
            "event_index": pos,
            "key": admission.get("key"),
            "input_ack_ns": admission.get("input_ack_ns"),
            "candidate_count": len(candidates),
            "candidate_event_indices": [j for j, _ in candidates],
            "candidate_id_steps": [[h.get("id"), h.get("step")]
                                    for _, h in candidates],
        })
    histogram = {}
    for row in rows:
        label = str(row["candidate_count"])
        histogram[label] = histogram.get(label, 0) + 1
    unique = sum(row["candidate_count"] == 1 for row in rows)
    ambiguous = sum(row["candidate_count"] > 1 for row in rows)
    unmatched = sum(row["candidate_count"] == 0 for row in rows)
    return events, admissions, holds, rows, histogram, unique, ambiguous, unmatched


def audit(result_path):
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    events, admissions, holds, rows, histogram, unique, ambiguous, unmatched = (
        independently_reconstruct(raw))
    counts = result.get("counts", {})
    checks = {
        "pinned_source_matches": digest == PIN == result.get("source_sha256"),
        "source_counts_match": (len(events), len(admissions), len(holds)) ==
        (634, 39, 28) == (counts.get("events"), counts.get("admissions"),
                          counts.get("aggregate_holds")),
        "all_candidate_rows_match": result.get("rows") == rows,
        "candidate_histogram_matches": result.get("candidate_count_histogram") == histogram,
        "unique_summary_matches": type(result.get("unique")) is int and
        result["unique"] == unique,
        "ambiguous_summary_matches": type(result.get("ambiguous")) is int and
        result["ambiguous"] == ambiguous,
        "unmatched_summary_matches": type(result.get("unmatched")) is int and
        result["unmatched"] == unmatched,
        "decision_matches_gate": result.get("decision") ==
        ("PASS_HEURISTIC_NONUNIQUENESS_SCOPED"
         if len(events) == 634 and len(admissions) == 39 and len(holds) == 28 and
         ambiguous > 0 else "FAIL_OR_HOLD"),
    }
    return {
        "schema": "map01-admission-hold-a04-summary-audit-v2",
        "pass": all(checks.values()),
        "checks": checks,
        "recomputed": {"events": len(events), "admissions": len(admissions),
                       "aggregate_holds": len(holds), "unique": unique,
                       "ambiguous": ambiguous, "unmatched": unmatched,
                       "candidate_count_histogram": histogram},
        "scope": "raw event and saved-result consistency only; candidate matches are not identity proof",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", default=str(PKG / "RESULT.json"))
    parser.add_argument("--output", default=str(PKG / "AUDIT_V2.json"))
    args = parser.parse_args()
    report = audit(args.result)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
