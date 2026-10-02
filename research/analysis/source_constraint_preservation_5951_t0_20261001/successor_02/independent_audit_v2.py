"""Corrected independent adjudication of allocation-01's immutable output."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
ORACLE = {
    "exact_copy": ("PASS", set()),
    "paraphrase": ("PASS", set()),
    "omitted_prohibition": ("FAIL", {"SOURCE_CLAUSE_OMITTED"}),
    "weakened_conditional": ("FAIL", {"CLAUSE_WEAKENED"}),
    "invented_permission": ("FAIL", {"SOURCE_CLAUSE_OMITTED", "UNSUPPORTED_DERIVATION"}),
    "authenticated_supersession": ("PASS", set()),
    "genuine_ambiguity": ("PASS", set()),
    "source_span_mismatch": ("FAIL", {"SOURCE_CLAUSE_OMITTED", "SOURCE_SPAN_MISMATCH"}),
}


def main():
    raw_path = ROOT / "candidate.raw.json"
    raw_bytes = raw_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest().upper()
    expected_digest = "B4A50872703F50C51747976925C33A72F5D7471D0F7FB94C9CACCEA5937DB9D1"
    errors = []
    if digest != expected_digest:
        errors.append("RAW_INPUT_HASH_MISMATCH")
    rows = json.loads(raw_bytes)
    by_id = {r["case_id"]: r for r in rows}
    if set(by_id) != set(ORACLE):
        errors.append("CASE_SET_MISMATCH")
    for cid, (outcome, classes) in ORACLE.items():
        got = by_id.get(cid, {}).get("candidate", {})
        if got.get("outcome") != outcome or set(got.get("errors", [])) != classes:
            errors.append(f"{cid}:INDEPENDENT_DECISION_MISMATCH")
    report = {"status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT", "raw_sha256": digest, "independent_oracle_cases": len(ORACLE), "errors": errors}
    (Path(__file__).parent / "audit.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
