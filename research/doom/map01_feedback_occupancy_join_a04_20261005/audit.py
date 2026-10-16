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
    rows = [json.loads(line) for line in raw.splitlines()]
    admits = [(n, e) for n, e in enumerate(rows) if e.get("event") == "input_admission"]
    aggregate = [(n, e) for n, e in enumerate(rows) if e.get("event") == "keys_held"]
    result = json.loads((PKG / "RESULT.json").read_text(encoding="utf-8"))
    # Independent implementation: index aggregate receipts by key, then retain
    # receipts after each admission's stream position.
    receipts_by_key = {}
    for position, receipt in aggregate:
        for key in set(receipt.get("keys", [])):
            receipts_by_key.setdefault(key, []).append((position, receipt))
    expected_rows = []
    for position, admission in admits:
        choices = [(p, r) for p, r in receipts_by_key.get(admission["key"], []) if p > position]
        expected_rows.append((position, len(choices), [p for p, _ in choices], [[r.get("id"), r.get("step")] for _, r in choices]))
    actual_rows = [(r["event_index"], r["candidate_count"], r["candidate_event_indices"], r["candidate_id_steps"]) for r in result["rows"]]
    checks = {
        "pinned_source_matches": digest == PIN == result["source_sha256"],
        "source_counts_match": (len(rows), len(admits), len(aggregate)) == (634, 39, 28) == (result["counts"]["events"], result["counts"]["admissions"], result["counts"]["aggregate_holds"]),
        "all_row_candidates_match_independent_reconstruction": actual_rows == expected_rows,
        "histogram_reconciles": sum(int(k) * v for k, v in result["candidate_count_histogram"].items()) == sum(len(x[2]) for x in expected_rows) and sum(result["candidate_count_histogram"].values()) == len(admits),
        "ambiguous_admissions_present": any(n > 1 for _, n, _, _ in expected_rows),
        "result_decision_matches_gate": result["decision"] == "PASS_HEURISTIC_NONUNIQUENESS_SCOPED",
    }
    report = {"schema": "map01-admission-hold-candidate-count-a04-independent-audit-v1", "pass": all(checks.values()), "checks": checks, "counts": {"events": len(rows), "admissions": len(admits), "aggregate_holds": len(aggregate)}, "summary": {"unique": sum(n == 1 for _, n, _, _ in expected_rows), "ambiguous": sum(n > 1 for _, n, _, _ in expected_rows), "unmatched": sum(n == 0 for _, n, _, _ in expected_rows)}}
    (PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
