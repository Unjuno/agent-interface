#!/usr/bin/env python3
"""Audit the A01 retained result and corruption receipts from source/raw files."""
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = next(p for p in PKG.parents if (p / ".git").exists())
SOURCE = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
PIN = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    raw = SOURCE.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    admissions = [(i, row) for i, row in enumerate(events)
                  if row.get("event") == "input_admission"]
    holds = [(i, row) for i, row in enumerate(events)
             if row.get("event") == "keys_held"]
    holds_by_key = {}
    for index, row in holds:
        for key in set(row.get("keys", [])):
            holds_by_key.setdefault(key, []).append(index)
    candidate_counts = [
        sum(index > admission_index
            for index in holds_by_key.get(admission["key"], ()))
        for admission_index, admission in admissions
    ]
    expected = {
        "events": len(events), "admissions": len(admissions),
        "aggregate_holds": len(holds),
        "unique": sum(count == 1 for count in candidate_counts),
        "ambiguous": sum(count > 1 for count in candidate_counts),
        "unmatched": sum(count == 0 for count in candidate_counts),
    }
    result = read_json(PKG / "RESULT.json")
    original_audit = read_json(PKG / "AUDIT.json")
    checks = {
        "source_sha_matches_freeze": hashlib.sha256(raw).hexdigest() == PIN,
        "raw_input_counts_match": expected == {
            "events": 634, "admissions": 39, "aggregate_holds": 28,
            "unique": 6, "ambiguous": 33, "unmatched": 0},
        "candidate_summary_matches_raw": all(result.get(key) == value
                                             for key, value in expected.items()
                                             if key in ("unique", "ambiguous", "unmatched")),
        "pristine_original_audit_passed": original_audit.get("pass") is True and
        all(original_audit.get("checks", {}).values()),
        "all_mutations_change_only_named_summary": True,
        "original_auditor_false_accepts_all_mutations": True,
        "v2_rejects_only_named_summary_mismatches": True,
    }
    expected_mutations = {"unique": 0, "ambiguous": 0, "unmatched": 39}
    for field, replacement in expected_mutations.items():
        case = PKG / "corruptions" / field
        mutated = read_json(case / "RESULT.json")
        original = read_json(case / "AUDIT.json")
        repaired = read_json(case / "AUDIT_V2.json")
        keys = set(result) | set(mutated)
        changed = {key for key in keys if result.get(key) != mutated.get(key)}
        checks["all_mutations_change_only_named_summary"] &= (
            changed == {field} and mutated.get(field) == replacement)
        checks["original_auditor_false_accepts_all_mutations"] &= (
            (PKG / "raw" / f"ORIGINAL_AUDITOR_{field}.exit.txt").read_text().strip() == "0" and
            original.get("pass") is True and all(original.get("checks", {}).values()))
        check_name = f"{field}_summary_matches"
        checks["v2_rejects_only_named_summary_mismatches"] &= (
            (PKG / "raw" / f"AUDIT_V2_{field}.exit.txt").read_text().strip() == "1" and
            repaired.get("pass") is False and
            repaired.get("checks", {}).get(check_name) is False and
            all(value is True for name, value in repaired.get("checks", {}).items()
                if name != check_name))

    report = {
        "schema": "map01-a04-audit-followup-independent-raw-audit-v1",
        "pass": all(checks.values()),
        "checks": checks,
        "reconstructed": expected,
        "summary_corruptions": expected_mutations,
        "decision": "PASS_RAW_OUTPUTS_RECONCILED" if all(checks.values()) else "FAIL",
        "scope": "source-bound audit mutation evidence only; no true identity or live-control inference",
    }
    output = PKG / "INDEPENDENT_AUDIT.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
