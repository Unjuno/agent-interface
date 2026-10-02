"""Independent outcome-set audit for the frozen strong-baseline table."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
EXPECTED = {
    "exact_copy": "PASS", "paraphrase": "PASS", "omitted_prohibition": "FAIL",
    "weakened_conditional": "FAIL", "invented_permission": "FAIL",
    "authenticated_supersession": "FAIL", "genuine_ambiguity": "PASS",
    "source_span_mismatch": "FAIL",
}


def main():
    raw = (HERE / "baseline_v3.raw.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    errors = []
    if digest != "809488625C59F4437650B17BB7C793AA52060F1FE3C6ABCF9D05C6B4F8559032":
        errors.append("BASELINE_RAW_HASH_MISMATCH")
    report = json.loads(raw)
    rows = {r["case_id"]: r for r in report.get("rows", [])}
    if set(rows) != set(EXPECTED):
        errors.append("CASE_SET_MISMATCH")
    for case_id, outcome in EXPECTED.items():
        row = rows.get(case_id, {})
        if row.get("expected") != outcome or row.get("baseline", {}).get("outcome") != outcome:
            errors.append(f"{case_id}:OUTCOME_MISMATCH")
    result = {"status": "PASS_INDEPENDENT_BASELINE_AUDIT" if not errors else "FAIL_INDEPENDENT_BASELINE_AUDIT", "input_sha256": digest, "cases": len(EXPECTED), "errors": errors}
    (HERE / "baseline_audit.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
