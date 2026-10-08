"""Read-only raw audit with an oracle separate from the construction candidate."""

import hashlib
import json
from pathlib import Path

from oracle import decide


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw_host.json"
CORPUS = ROOT / "cases.json"
TOP_KEYS = {"schema", "corpus_sha256", "invocation", "dispatch_count", "rows"}
ROW_KEYS = {"case_id", "input", "decision"}
DECISION_KEYS = {
    "aggregate_status", "decisions", "dispatch_count", "authority",
}
DETAIL_KEYS = {
    "check_id", "verifier_id", "requested_version", "primitive", "input_role",
    "subject_ref", "criticality", "deadline", "budget_class", "check_fallback",
    "output_role", "side_effect_class", "authority", "mode", "cold_cost_estimate",
    "warm_cost_estimate", "selected_cost_estimate", "cost_unit", "cost_provenance",
    "declared_cost_provenance",
    "latency_bound", "latency_unit", "resource_class", "category", "failure_modes",
    "fallback", "status", "reason",
    "descriptor_snapshot",
}


def audit(raw=None, corpus_bytes=None):
    raw = json.loads(RAW.read_text(encoding="utf-8")) if raw is None else raw
    corpus_bytes = CORPUS.read_bytes() if corpus_bytes is None else corpus_bytes
    corpus = json.loads(corpus_bytes)
    errors = []
    if (set(corpus) != {"schema", "source_issue", "cost_note", "cases"}
            or corpus.get("schema") != "verifier_registry_5273_t0_v6.corpus.v1"
            or corpus.get("source_issue") != 5273):
        return ["corpus_schema"]
    if set(raw) != TOP_KEYS or raw.get("schema") != "verifier_registry_5273_t0_v6.raw.v1":
        errors.append("raw_schema")
        return errors
    if raw["invocation"] != "HOST_OFFLINE_CONSTRUCTION_ONLY" or raw["dispatch_count"] != 0:
        errors.append("execution_boundary")
    if raw["corpus_sha256"] != hashlib.sha256(corpus_bytes).hexdigest():
        errors.append("corpus_binding")
    expected = {row["case_id"]: row for row in corpus["cases"]}
    if len(raw["rows"]) != len(expected):
        errors.append("row_count")
    seen = set()
    for row in raw["rows"]:
        if set(row) != ROW_KEYS:
            errors.append("row_schema")
            continue
        key = row["case_id"]
        if key in seen or key not in expected:
            errors.append("case_identity")
            continue
        seen.add(key)
        case = expected[key]
        wanted_input = {name: case[name] for name in ("ir", "assignments", "registry", "resources")}
        if row["input"] != wanted_input:
            errors.append("input_binding:" + key)
            continue
        decision = row["decision"]
        if set(decision) != DECISION_KEYS:
            errors.append("decision_schema:" + key)
            continue
        oracle = decide(case)
        if (decision["aggregate_status"], decision["dispatch_count"], decision["authority"]) != (
                oracle["aggregate_status"], 0, "NONE"):
            errors.append("aggregate_or_boundary:" + key)
        if len(decision["decisions"]) != len(oracle["decisions"]):
            errors.append("decision_count:" + key)
            continue
        for got, want in zip(decision["decisions"], oracle["decisions"]):
            if (got.get("check_id"), got.get("status"), got.get("reason")) != (
                    want["check_id"], want["status"], want["reason"]):
                errors.append("oracle_mismatch:" + key)
                continue
            if (got["status"], got["reason"]) != (
                    case["expected_status"], case["expected_reason"]):
                errors.append("frozen_expectation_mismatch:" + key)
            has_descriptor = bool(case["registry"])
            if has_descriptor:
                if set(got) != DETAIL_KEYS:
                    errors.append("detail_schema:" + key)
                    continue
                check, assignment, descriptor = (case["ir"]["checks"][0],
                    case["assignments"][0], case["registry"][0])
                if (got["primitive"], got["input_role"], got["subject_ref"],
                    got["criticality"], got["deadline"], got["check_fallback"]) != (
                    check["primitive"], check["required_evidence_role"], check["subject_ref"],
                    check["criticality"], check["deadline"], check["fallback"]):
                    errors.append("ir_binding:" + key)
                if (got["verifier_id"], got["requested_version"], got["mode"],
                    got["output_role"]) != (descriptor["verifier_id"],
                    assignment["requested_version"], assignment["mode"], assignment["output_role"]):
                    errors.append("assignment_binding:" + key)
                if (got["authority"], got["cost_provenance"],
                    got["declared_cost_provenance"],
                    got["cold_cost_estimate"], got["warm_cost_estimate"]) != (
                    "NONE", "DECLARED_ESTIMATE_NOT_MEASUREMENT", descriptor["cost_provenance"],
                    descriptor["cold_cost"], descriptor["warm_cost"]):
                    errors.append("descriptor_binding:" + key)
                if got["descriptor_snapshot"] != descriptor:
                    errors.append("descriptor_snapshot_binding:" + key)
    if seen != set(expected):
        errors.append("missing_cases")
    return sorted(set(errors))


if __name__ == "__main__":
    failures = audit()
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "errors": failures}))
    raise SystemExit(bool(failures))
