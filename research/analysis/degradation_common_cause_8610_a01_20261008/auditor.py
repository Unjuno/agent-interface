"""Independent raw-spec auditor for the finite degradation-contract fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMPONENTS = {
    "planner": ["planner_process", "planner_backend"],
    "raw_observation": ["capture_source", "raw_adapter"],
    "semantic_observation": ["capture_source", "shared_parser", "semantic_scheduler"],
    "verifier": ["capture_source", "shared_parser", "semantic_scheduler"],
    "effect_confirmation": ["effect_source", "shared_parser", "effect_process"],
    "telemetry": ["event_loop", "telemetry_sink"],
    "authority": ["authority_owner"],
    "release": ["release_channel"],
}
OPERATIONS = [
    {"id": "inspect_raw", "requires": ["raw_observation", "authority", "release"], "evidence": ["raw_fresh", "raw_intact"], "source": "raw_observation", "claim": "RAW_OBSERVED"},
    {"id": "present_semantics", "requires": ["semantic_observation", "verifier", "authority", "release"], "evidence": ["semantic_fresh", "semantic_intact"], "source": "semantic_observation", "claim": "SEMANTIC_VERIFIED"},
    {"id": "preview_plan", "requires": ["planner", "semantic_observation", "verifier", "authority", "release"], "evidence": ["semantic_fresh", "semantic_intact"], "source": "planner", "claim": "PREVIEW_ONLY"},
    {"id": "show_effect_receipt", "requires": ["effect_confirmation", "verifier", "authority", "release"], "evidence": ["effect_fresh", "effect_intact"], "source": "effect_confirmation", "claim": "EFFECT_VERIFIED"},
]
BINARY_FULL_ROUTE = ["planner", "raw_observation", "semantic_observation", "verifier", "effect_confirmation", "telemetry", "authority", "release"]
CASE_IDS = [
    "healthy",
    "independent_telemetry_loss",
    "common_capture_loss",
    "common_semantic_scheduler_stall",
    "common_parser_lineage_corruption",
    "independent_effect_process_loss",
    "stale_semantic_evidence",
    "release_channel_loss",
    "authority_owner_loss",
]


def _row(operation: dict) -> dict:
    return {
        "operation": operation["id"],
        "source": operation["source"],
        "claim": operation["claim"],
        "freshness": "CURRENT",
    }


def _service_state(case: dict) -> dict[str, bool]:
    unavailable = set(case.get("failed_dependencies", [])) | set(case.get("corrupted_dependencies", []))
    return {name: not bool(set(dependencies) & unavailable) for name, dependencies in COMPONENTS.items()}


def _usable(case: dict, operation: dict, services: dict[str, bool]) -> bool:
    evidence = case.get("evidence", {})
    return all(services.get(name, False) for name in operation["requires"]) and all(evidence.get(name) is True for name in operation["evidence"])


def audit(spec: dict, candidate: dict) -> dict:
    errors = []
    if not isinstance(spec, dict) or spec.get("schema") != "8610-degradation-spec-v1" or spec.get("version") != "degradation-v1":
        errors.append("spec_identity")
    if spec.get("components") != COMPONENTS:
        errors.append("component_dependency_graph")
    if spec.get("operations") != OPERATIONS:
        errors.append("operation_contract_table")
    if spec.get("binary_full_route") != BINARY_FULL_ROUTE:
        errors.append("binary_route_definition")
    scenarios = spec.get("scenarios") if isinstance(spec, dict) else None
    if not isinstance(scenarios, list) or [c.get("id") for c in scenarios if isinstance(c, dict)] != CASE_IDS:
        errors.append("scenario_identity_or_order")
        scenarios = scenarios if isinstance(scenarios, list) else []
    if not isinstance(candidate, dict) or candidate.get("schema") != "8610-candidate-v1" or set(candidate) != {"schema", "cases"}:
        errors.append("candidate_schema")
    rows = candidate.get("cases", []) if isinstance(candidate, dict) else []
    if not isinstance(rows, list) or len(rows) != len(CASE_IDS):
        errors.append("candidate_case_denominator")
        rows = rows if isinstance(rows, list) else []
    actual_by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("case_id"), str) or row["case_id"] in actual_by_id:
            errors.append("candidate_case_identity")
            continue
        actual_by_id[row["case_id"]] = row

    additional = 0
    unsafe_rejections = 0
    authority_inflation = 0
    false_effect_claims = 0
    release_verified = 0
    allowed_ids = {operation["id"] for operation in OPERATIONS}
    by_id = {operation["id"]: operation for operation in OPERATIONS}
    for case in scenarios:
        if not isinstance(case, dict) or case.get("id") not in CASE_IDS:
            continue
        case_id = case["id"]
        actual = actual_by_id.get(case_id)
        if actual is None:
            errors.append(case_id + ":missing_case")
            continue
        if set(actual) != {"case_id", "binary", "contract", "silent_substitution", "release_obligation"}:
            errors.append(case_id + ":case_fields")
        services = _service_state(case)
        contract = [_row(op) for op in OPERATIONS if _usable(case, op, services)]
        binary_ready = all(services.get(name, False) for name in BINARY_FULL_ROUTE)
        evidence = case.get("evidence", {})
        binary_ready = binary_ready and all(value is True for value in evidence.values())
        binary = contract if binary_ready else []
        silent = list(contract)
        raw_usable = (
            services.get("raw_observation", False)
            and services.get("authority", False)
            and services.get("release", False)
            and evidence.get("raw_fresh") is True
            and evidence.get("raw_intact") is True
        )
        semantic_supported = any(row["operation"] == "present_semantics" for row in contract)
        if raw_usable and not semantic_supported:
            silent.append({"operation": "present_semantics", "source": "raw_observation", "claim": "SEMANTIC_VERIFIED", "freshness": "CURRENT"})
        for field, expected in (("binary", binary), ("contract", contract), ("silent_substitution", silent)):
            if actual.get(field) != expected:
                errors.append(case_id + ":" + field)
        if actual.get("release_obligation") == "MANDATORY_RELEASE":
            release_verified += 1
        else:
            errors.append(case_id + ":release_obligation")
        additional += sum(1 for row in contract if row not in binary)
        unsafe_rejections += sum(1 for row in silent if row not in contract)
        for row in actual.get("contract", []) if isinstance(actual.get("contract"), list) else []:
            if not isinstance(row, dict):
                authority_inflation += 1
                continue
            if row.get("operation") not in allowed_ids:
                authority_inflation += 1
            if row.get("claim") == "EFFECT_VERIFIED" and row.get("operation") != "show_effect_receipt":
                false_effect_claims += 1

    if set(actual_by_id) != set(CASE_IDS):
        errors.append("candidate_case_coverage")
    if additional < 1:
        errors.append("no_incremental_supported_outcome")
    if unsafe_rejections != 3:
        errors.append("unsafe_control_not_rejected")
    if authority_inflation:
        errors.append("authority_inflation")
    if false_effect_claims:
        errors.append("false_effect_claim")
    if release_verified != len(CASE_IDS):
        errors.append("release_coverage")
    errors = sorted(set(errors))
    passed = not errors
    return {
        "schema": "8610-audit-v1",
        "audit_integrity": "PASS" if passed else "FAIL",
        "status": "PASS_METHOD_SCOPED" if passed else "FAIL_METHOD",
        "errors": errors,
        "cases_reconstructed": len(actual_by_id),
        "additional_supported_outcomes": additional,
        "unsafe_control_rejections": unsafe_rejections,
        "authority_inflation": authority_inflation,
        "false_effect_claims": false_effect_claims,
        "release_obligations_verified": release_verified,
        "dispatches": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit(spec, candidate)
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(f"AUDIT_COMPLETE {result['audit_integrity']} errors={len(result['errors'])}")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
