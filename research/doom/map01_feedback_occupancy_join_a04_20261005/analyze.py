import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PKG = Path(__file__).resolve().parent
SOURCE = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
PIN = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"


def main():
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PIN:
        raise SystemExit("HOLD_SOURCE_HASH_MISMATCH")
    events = [json.loads(line) for line in raw.splitlines()]
    admissions = [i for i, e in enumerate(events) if e.get("event") == "input_admission"]
    holds = [(i, e) for i, e in enumerate(events) if e.get("event") == "keys_held"]
    rows = []
    for index in admissions:
        admission = events[index]
        eligible = [(j, h) for j, h in holds if j > index and admission["key"] in h.get("keys", [])]
        rows.append({
            "event_index": index,
            "key": admission["key"],
            "input_ack_ns": admission["input_ack_ns"],
            "candidate_count": len(eligible),
            "candidate_event_indices": [j for j, _ in eligible],
            "candidate_id_steps": [[h.get("id"), h.get("step")] for _, h in eligible],
        })
    histogram = {}
    for row in rows:
        label = str(row["candidate_count"])
        histogram[label] = histogram.get(label, 0) + 1
    result = {
        "schema": "map01-admission-hold-candidate-count-a04-v1",
        "decision": "PASS_HEURISTIC_NONUNIQUENESS_SCOPED" if len(events) == 634 and len(rows) == 39 and len(holds) == 28 and any(r["candidate_count"] > 1 for r in rows) else "FAIL_OR_HOLD",
        "source_sha256": digest,
        "counts": {"events": len(events), "admissions": len(rows), "aggregate_holds": len(holds)},
        "candidate_count_histogram": histogram,
        "unique": sum(r["candidate_count"] == 1 for r in rows),
        "ambiguous": sum(r["candidate_count"] > 1 for r in rows),
        "unmatched": sum(r["candidate_count"] == 0 for r in rows),
        "rows": rows,
        "limitations": ["A candidate row is not an identity proof.", "Only raw event order plus key membership is used.", "No undocumented runtime-order invariant is assumed.", "No physical release, useful task feedback, causal effect, recovery, or live result is inferred."],
    }
    (PKG / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("schema", "decision", "source_sha256", "counts", "candidate_count_histogram", "unique", "ambiguous", "unmatched")}, indent=2))


if __name__ == "__main__":
    main()
