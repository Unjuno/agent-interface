import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists() and (p / "research/doom").exists())
PKG = Path(__file__).resolve().parent
SRC = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004"


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    result = json.loads((PKG / "RESULT.json").read_text())
    events = [json.loads(line) for line in (SRC / "events.jsonl").read_text().splitlines()]
    admissions = [e for e in events if e.get("event") == "input_admission"]
    holds = [e for e in events if e.get("event") == "keys_held"]
    candidates = [sum(h.get("input_ack_ns", -1) >= a["input_ack_ns"] and a["key"] in h.get("keys", []) for h in holds) for a in admissions]
    fixture_matches = [h["id"] for h in [
        {"id": "A", "input_ack_ns": 20, "keys": ["space"]},
        {"id": "B", "input_ack_ns": 30, "keys": ["space"]},
    ] if h["input_ack_ns"] >= 10 and "space" in h["keys"]]
    checks = {
        "source_hashes_match": all(sha(ROOT / rel) == digest for digest, rel in (x.split("  ", 1) for x in (PKG / "SOURCE_SHA256SUMS.txt").read_text().splitlines())),
        "counts_match": (len(events), len(admissions), len(holds)) == (634, 39, 28) == (result["counts"]["events"], result["counts"]["admissions"], result["counts"]["aggregate_holds"]),
        "all_admission_candidate_counts_match": candidates == [x["candidate_count"] for x in result["admissions"]],
        "at_least_one_ambiguous_admission": any(n > 1 for n in candidates),
        "unique_count_matches": sum(n == 1 for n in candidates) == result["uniquely_joinable"],
        "step_set_checks_retained": len(result["step_set_checks"]) == 28 and result["inconsistent_step_key_sets"] == sum(not x["consistent"] for x in result["step_set_checks"]),
        "identity_ambiguity_counterexample_detected": fixture_matches == result["ambiguity_counterexample"]["admissible_identity_assignments"],
    }
    report = {"schema": "map01-admission-hold-identity-ambiguity-a03-independent-audit-v1", "pass": all(checks.values()), "checks": checks, "summary": {"unique": sum(n == 1 for n in candidates), "ambiguous": sum(n > 1 for n in candidates), "unmatched": sum(n == 0 for n in candidates), "inconsistent_step_key_sets": result["inconsistent_step_key_sets"]}}
    (PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__": main()
