"""Separate raw-only CLI audit for the experimental binding candidate report."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_oracle import reconstruct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", required=True, type=Path)
    parser.add_argument("--candidate-report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")

    trace_bytes = args.traces.read_bytes()
    candidate_bytes = args.candidate_report.read_bytes()
    traces = json.loads(trace_bytes)
    candidate = json.loads(candidate_bytes)
    errors = []
    if candidate.get("schema") != "w2-lease-actuation-candidate-cli-v1":
        errors.append("candidate_schema_mismatch")
    if candidate.get("effective_trace_sha256") != digest(trace_bytes):
        errors.append("effective_trace_hash_mismatch")

    raw_cases = traces.get("cases", [])
    candidate_cases = candidate.get("cases", [])
    raw_ids = [c.get("case_id") for c in raw_cases]
    report_ids = [c.get("case_id") for c in candidate_cases]
    if raw_ids != report_ids:
        errors.append("case_order_or_identity_mismatch")

    reconstructed = []
    for raw_case, candidate_case in zip(raw_cases, candidate_cases):
        rows = reconstruct(raw_case.get("events", []))
        reconstructed.append({
            "case_id": raw_case.get("case_id"),
            "binding_decisions": rows,
        })
        if candidate_case.get("binding_decisions") != rows:
            errors.append(f"candidate_raw_disagreement:{raw_case.get('case_id')}")

    result = {
        "schema": "w2-lease-actuation-independent-cli-audit-v1",
        "disposition": "PASS_BINDING_RAW_AUDIT_SCOPED" if not errors else "FAIL_BINDING_RAW_AUDIT",
        "effective_trace_sha256": digest(trace_bytes),
        "candidate_report_sha256": digest(candidate_bytes),
        "case_count": len(raw_cases),
        "edge_rows_reconstructed": sum(len(c["binding_decisions"]) for c in reconstructed),
        "candidate_oracle_disagreements": sum(e.startswith("candidate_raw_disagreement:") for e in errors),
        "errors": errors,
        "reconstructed": reconstructed,
        "limits": [
            "This audit reconstructs only actuation-binding dispositions from raw event rows.",
            "It does not validate lease time windows, owner/session, clock conversion, or broader trace invariants.",
        ],
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "errors": errors, "case_count": len(raw_cases)}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
