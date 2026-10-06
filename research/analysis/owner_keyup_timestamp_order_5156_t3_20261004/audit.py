"""Independent raw-only integrity audit and hypothesis classification."""
import copy
import hashlib
import json
import sys
from pathlib import Path


def classify(cases_doc, raw, analyzer_sha):
    errors, findings = [], []
    if raw.get("schema") != "owner-keyup-timestamp-order-raw-v1":
        errors.append("raw_schema")
    if raw.get("allocation") != cases_doc.get("allocation"):
        errors.append("allocation")
    if raw.get("analyzer_sha256") != analyzer_sha:
        errors.append("analyzer_identity")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(cases_doc.get("cases", [])):
        return errors + ["row_inventory"], findings
    by_id = {row.get("case_id"):row for row in rows if isinstance(row, dict)}
    for case in cases_doc["cases"]:
        row = by_id.get(case["id"])
        if row is None:
            errors.append("missing:" + case["id"])
            continue
        out = row.get("analyzer_output", {})
        ordered = (case["admitted_ns"] <= case["input_ack_ns"] <=
                   case["release_call_started_ns"] <= case["release_call_returned_ns"])
        if case["expected_ready"] is not ordered:
            errors.append("bad_frozen_oracle:" + case["id"])
        observed = out.get("measurement_ready")
        if type(observed) is not bool:
            errors.append("readiness_type:" + case["id"])
        elif observed is not case["expected_ready"]:
            findings.append("readiness_mismatch:" + case["id"])
        holds = out.get("holds", [])
        if len(holds) != 1:
            errors.append("hold_count:" + case["id"])
            continue
        lower = (case["release_call_started_ns"]-case["input_ack_ns"])/1e6
        upper = (case["release_call_returned_ns"]-case["admitted_ns"])/1e6
        if holds[0].get("retained_lower_ms") != lower or holds[0].get("retained_upper_ms") != upper:
            errors.append("bound_arithmetic:" + case["id"])
    return errors, findings


def hypothesis_outcome(findings):
    return "FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED" if findings else "PASS_ORDER_GATE_SCOPED"


def main():
    cases_path, raw_path, output_path = map(Path, sys.argv[1:4])
    cases_doc = json.loads(cases_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    analyzer_sha = hashlib.sha256(Path("source/analyze_map01_direct_retained_input_v1.py").read_bytes()).hexdigest()
    errors, findings = classify(cases_doc, raw, analyzer_sha)
    baseline_outcome = hypothesis_outcome(findings)

    mutations = []
    missing = copy.deepcopy(raw); missing["rows"].pop()
    mutations.append((missing, "integrity"))
    wrong_ready = copy.deepcopy(raw)
    next(r for r in wrong_ready["rows"] if r["case_id"] == "ack_before_admission")["analyzer_output"]["measurement_ready"] = False
    mutations.append((wrong_ready, "classification"))
    wrong_hash = copy.deepcopy(raw); wrong_hash["analyzer_sha256"] = "0"*64
    mutations.append((wrong_hash, "integrity"))
    wrong_bound = copy.deepcopy(raw)
    next(r for r in wrong_bound["rows"] if r["case_id"] == "ordinary_order")["analyzer_output"]["holds"][0]["retained_lower_ms"] += 1
    mutations.append((wrong_bound, "integrity"))
    rejected = []
    for mutation, kind in mutations:
        mutation_errors, mutation_findings = classify(cases_doc, mutation, analyzer_sha)
        if kind == "integrity":
            rejected.append(bool(mutation_errors))
        else:
            rejected.append(hypothesis_outcome(mutation_findings) != baseline_outcome)

    if not all(rejected):
        errors.append("mutation_control")
    result = {
        "schema":"owner-keyup-timestamp-order-audit-v2",
        "audit_status":"PASS_RAW_AND_CONTROLS" if not errors else "STOP_AUDIT_INTEGRITY",
        "hypothesis_outcome":baseline_outcome,
        "finding_case_ids":[item.split(":",1)[1] for item in findings],
        "case_count":len(raw.get("rows", [])),
        "mutation_controls":len(rejected),
        "mutation_rejections":sum(rejected),
        "integrity_errors":errors,
        "scientific_findings":findings,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
