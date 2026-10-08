"""Reconstruct close-order decisions from raw rows in a separate process."""
import argparse
import hashlib
import json
from pathlib import Path

from close_order_oracle import reconstruct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    raw = args.traces.read_bytes()
    candidate_raw = args.candidate.read_bytes()
    traces, candidate = json.loads(raw), json.loads(candidate_raw)
    errors = []
    if candidate.get("schema") != "w2-lease-close-candidate-report-v1":
        errors.append("candidate_schema_mismatch")
    if candidate.get("trace_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("trace_hash_mismatch")
    raw_cases = traces.get("cases", [])
    proposed = candidate.get("cases", [])
    if [c.get("case_id") for c in raw_cases] != [c.get("case_id") for c in proposed]:
        errors.append("case_identity_or_order_mismatch")
    reconstructions = []
    for raw_case, proposed_case in zip(raw_cases, proposed):
        rows = reconstruct(raw_case.get("events", []))
        reconstructions.append({"case_id": raw_case.get("case_id"), "decisions": rows})
        if rows != proposed_case.get("decisions"):
            errors.append("candidate_raw_disagreement:" + str(raw_case.get("case_id")))
    audit = {
        "schema": "w2-lease-close-independent-raw-audit-v1",
        "disposition": "PASS_CLOSE_ORDER_RAW_AUDIT_SCOPED" if not errors else "FAIL_CLOSE_ORDER_RAW_AUDIT",
        "trace_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_raw).hexdigest(),
        "case_count": len(raw_cases),
        "decision_rows": sum(len(c["decisions"]) for c in reconstructions),
        "errors": errors,
        "reconstructed": reconstructions,
        "limits": ["Raw synthetic lease/actuation/close timing only; no live authority or runtime claim."],
    }
    args.out.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": audit["disposition"], "errors": errors, "case_count": len(raw_cases)}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
