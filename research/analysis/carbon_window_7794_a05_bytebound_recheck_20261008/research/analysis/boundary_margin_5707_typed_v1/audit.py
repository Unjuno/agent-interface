#!/usr/bin/env python3
"""Independent raw-only verifier for Issue #5707 typed-margin T0."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _classification(m: dict[str, Any]) -> str:
    if m["status"] == "UNKNOWN":
        return "UNKNOWN"
    lo, hi, threshold = m["lower"], m["upper"], m["threshold"]
    if not isinstance(lo, int) or isinstance(lo, bool) or not isinstance(hi, int) or isinstance(hi, bool):
        return "INVALID_INTERVAL_TYPE"
    if lo > hi:
        return "INVALID_INTERVAL_ORDER"
    if hi < threshold:
        return "CROSSED"
    if lo >= threshold:
        return "NOT_CROSSED"
    return "UNCERTAIN_INTERVAL_STRADDLES_THRESHOLD"


def reconstruct(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Recompute the complete opportunity ledger without candidate code."""
    seen: set[str] = set()
    expected: list[dict[str, Any]] = []
    grouped: dict[tuple[Any, ...], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for item in plan.get("opportunities", []):
        oid = item.get("opportunity_id")
        if not isinstance(oid, str) or not oid or oid in seen:
            raise ValueError("PLAN_OPPORTUNITY_ID_INVALID")
        seen.add(oid)
        margin = item.get("margin")
        rendered = None
        if margin is not None:
            rendered = dict(margin)
            rendered["classification"] = _classification(margin)
            key = (margin.get("purpose"), margin.get("boundary_kind"), margin.get("unit"),
                   margin.get("contract_id"), margin.get("contract_version"), margin.get("threshold"))
            grouped[key].append((oid, rendered))
        expected.append({
            "record_type": "opportunity",
            "allocation": plan["allocation"],
            "opportunity_id": oid,
            "disposition": item["disposition"],
            "forbidden_effect": item["forbidden_effect"],
            "actuation_margin_status": item["actuation_margin_status"],
            "margin": rendered,
        })
    if not seen:
        raise ValueError("PLAN_HAS_NO_OPPORTUNITIES")

    for key, pairs in sorted(grouped.items()):
        measured = [m for _, m in pairs if m["status"] == "MEASURED"]
        expected.append({
            "record_type": "typed_summary",
            "allocation": plan["allocation"],
            "purpose": key[0], "boundary_kind": key[1], "unit": key[2],
            "contract_id": key[3], "contract_version": key[4], "threshold": key[5],
            "opportunity_ids": sorted(oid for oid, _ in pairs),
            "observed_count": len(pairs),
            "measured_count": len(measured),
            "unknown_count": sum(m["status"] == "UNKNOWN" for _, m in pairs),
            "crossed_count": sum(m["classification"] == "CROSSED" for _, m in pairs),
            "not_crossed_count": sum(m["classification"] == "NOT_CROSSED" for _, m in pairs),
            "uncertain_count": sum(m["classification"] == "UNCERTAIN_INTERVAL_STRADDLES_THRESHOLD" for _, m in pairs),
            "minimum_interval": [min(m["lower"] for m in measured), min(m["upper"] for m in measured)] if measured else None,
        })
    return expected


def validate_records(plan: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    try:
        expected = reconstruct(plan)
    except (KeyError, TypeError, ValueError) as exc:
        return ["PLAN_RECONSTRUCTION:" + str(exc)]
    if records != expected:
        errors.append("RAW_LEDGER_DIFFERS_FROM_INDEPENDENT_RECONSTRUCTION")
    opportunity_rows = [r for r in records if r.get("record_type") == "opportunity"]
    summary_rows = [r for r in records if r.get("record_type") == "typed_summary"]
    if len(opportunity_rows) != 8:
        errors.append("OPPORTUNITY_DENOMINATOR_NOT_EIGHT")
    ids = [r.get("opportunity_id") for r in opportunity_rows]
    planned = [r.get("opportunity_id") for r in plan.get("opportunities", [])]
    if sorted(ids) != sorted(planned) or len(ids) != len(set(ids)):
        errors.append("OPPORTUNITY_ID_SET_OR_CARDINALITY_MISMATCH")
    if sum(r.get("forbidden_effect") is True for r in opportunity_rows) != 0:
        errors.append("FORBIDDEN_EFFECT_FIXTURE_NONZERO")
    if any("pooled_scalar" in r or "global_min_margin" in r for r in records):
        errors.append("CROSS_BOUNDARY_POOLED_SCALAR_PRESENT")
    by_id = {r.get("opportunity_id"): r for r in opportunity_rows}
    for oid in ("op-safe-stop", "op-blocked-negative-proposal"):
        if by_id.get(oid, {}).get("actuation_margin_status") != "NO_ACTUATION_MARGIN":
            errors.append("NO_ACTUATION_MARGIN_NOT_PRESERVED:" + oid)
    if by_id.get("op-blocked-negative-proposal", {}).get("margin", {}).get("purpose") != "proposal_admission":
        errors.append("BLOCKED_PROPOSAL_MARGIN_CONFLATED")
    if by_id.get("op-missing-timestamp", {}).get("margin", {}).get("classification") != "UNKNOWN":
        errors.append("MISSING_TIME_NOT_UNKNOWN")
    if by_id.get("op-exact-zero", {}).get("margin", {}).get("classification") != "NOT_CROSSED":
        errors.append("EXACT_ZERO_MISCLASSIFIED")
    if by_id.get("op-negative-crossing", {}).get("margin", {}).get("classification") != "CROSSED":
        errors.append("NEGATIVE_CROSSING_NOT_DETECTED")
    keys = {(r.get("purpose"), r.get("boundary_kind"), r.get("unit"), r.get("contract_id"), r.get("contract_version"), r.get("threshold")) for r in summary_rows}
    if len(summary_rows) != 4 or len(keys) != len(summary_rows):
        errors.append("TYPED_SUMMARY_GROUPING_INVALID")
    return errors


def corruption_controls(plan: dict[str, Any], raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tests: list[tuple[str, Any]] = []

    def mutate(name: str, fn: Any) -> None:
        changed = copy.deepcopy(raw)
        fn(changed)
        tests.append((name, changed))

    mutate("drop_opportunity", lambda rows: rows.pop(next(i for i, r in enumerate(rows) if r.get("opportunity_id") == "op-lease-positive")))
    mutate("duplicate_opportunity", lambda rows: rows.append(copy.deepcopy(next(r for r in rows if r.get("opportunity_id") == "op-lease-positive"))))
    def unit_swap(rows: list[dict[str, Any]]) -> None:
        next(r for r in rows if r.get("opportunity_id") == "op-hazard-clearance")["margin"]["unit"] = "ms"
    mutate("unit_swap", unit_swap)
    def pool_kinds(rows: list[dict[str, Any]]) -> None:
        next(r for r in rows if r.get("record_type") == "typed_summary")["boundary_kind"] = "mixed-boundaries"
    mutate("cross_kind_pool", pool_kinds)
    def safe_stop_positive(rows: list[dict[str, Any]]) -> None:
        row = next(r for r in rows if r.get("opportunity_id") == "op-safe-stop")
        row["actuation_margin_status"] = "MEASURED"
        row["margin"] = {"purpose": "actuation", "boundary_kind": "lease_expiry", "contract_id": "input-lease", "contract_version": "lease-v1", "unit": "ms", "threshold": 0, "status": "MEASURED", "lower": 999, "upper": 999, "classification": "NOT_CROSSED"}
    mutate("safe_stop_positive_margin", safe_stop_positive)
    def proposal_as_actuation(rows: list[dict[str, Any]]) -> None:
        next(r for r in rows if r.get("opportunity_id") == "op-blocked-negative-proposal")["actuation_margin_status"] = "MEASURED"
    mutate("proposal_actuation_conflation", proposal_as_actuation)
    def unknown_as_zero(rows: list[dict[str, Any]]) -> None:
        row = next(r for r in rows if r.get("opportunity_id") == "op-missing-timestamp")
        row["actuation_margin_status"] = "MEASURED"
        row["margin"].update(status="MEASURED", lower=0, upper=0, classification="NOT_CROSSED")
        row["margin"].pop("reason", None)
    mutate("unknown_to_zero", unknown_as_zero)
    def pool_versions(rows: list[dict[str, Any]]) -> None:
        row = next(r for r in rows if r.get("record_type") == "typed_summary" and r.get("contract_version") == "lease-v2")
        row["contract_version"] = "lease-v1"
    mutate("contract_version_pooling", pool_versions)
    def reverse_interval(rows: list[dict[str, Any]]) -> None:
        m = next(r for r in rows if r.get("opportunity_id") == "op-lease-positive")["margin"]
        m["lower"], m["upper"] = m["upper"], m["lower"]
    mutate("reversed_interval", reverse_interval)
    def zero_as_crossing(rows: list[dict[str, Any]]) -> None:
        next(r for r in rows if r.get("opportunity_id") == "op-exact-zero")["margin"]["classification"] = "CROSSED"
    mutate("zero_as_crossing", zero_as_crossing)
    return [{"name": name, "rejected": bool(validate_records(plan, changed))} for name, changed in tests]


def audit(plan: dict[str, Any], raw_bytes: bytes, execution: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    try:
        parsed = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "FAIL_TYPED_MARGIN_AUDIT", "errors": ["RAW_JSONL_INVALID:" + str(exc)]}
    errors.extend(validate_records(plan, parsed))
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    if execution is not None:
        if execution.get("allocation") != plan.get("allocation"):
            errors.append("EXECUTION_ALLOCATION_MISMATCH")
        if execution.get("frozen_main") != plan.get("frozen_main"):
            errors.append("EXECUTION_BASE_MISMATCH")
        if execution.get("candidate_exit") != 0:
            errors.append("CANDIDATE_EXIT_NOT_ZERO")
        if execution.get("raw_sha256") != raw_hash:
            errors.append("EXECUTION_RAW_HASH_MISMATCH")
        if execution.get("image_ref") != "python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8f910824d4e93bdce61e212c7e87168123ea3073b41a1a":
            errors.append("EXECUTION_IMAGE_REF_MISMATCH")
        if execution.get("image_id") != "sha256:febd0be41adb897a0ab8f1f1c693d8912669ea60c4940e076e9946b60e210ef0":
            errors.append("EXECUTION_IMAGE_ID_MISMATCH")
        if execution.get("platform") != "linux/amd64":
            errors.append("EXECUTION_PLATFORM_MISMATCH")
    controls = corruption_controls(plan, parsed)
    if len(controls) != 10 or not all(item["rejected"] for item in controls):
        errors.append("CORRUPTION_CONTROL_GATE_FAILED")
    return {
        "status": "PASS_TYPED_MARGIN_CONTRACT_SCOPED" if not errors else "FAIL_TYPED_MARGIN_AUDIT",
        "allocation": plan.get("allocation"),
        "opportunity_count": sum(row.get("record_type") == "opportunity" for row in parsed),
        "record_count": len(parsed),
        "typed_group_count": sum(row.get("record_type") == "typed_summary" for row in parsed),
        "unknown_margin_count": sum(row.get("status") == "UNKNOWN" for row in (r.get("margin") for r in parsed if r.get("record_type") == "opportunity") if row),
        "no_actuation_margin_count": sum(row.get("actuation_margin_status") == "NO_ACTUATION_MARGIN" for row in parsed if row.get("record_type") == "opportunity"),
        "forbidden_effect_count": sum(row.get("forbidden_effect") is True for row in parsed if row.get("record_type") == "opportunity"),
        "corruption_controls": controls,
        "corruption_controls_rejected": sum(item["rejected"] for item in controls),
        "errors": errors,
        "raw_sha256": raw_hash,
        "execution_sha256": hashlib.sha256(json.dumps(execution, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if execution is not None else None,
        "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    execution = json.loads(args.execution.read_text(encoding="utf-8"))
    result = audit(plan, args.raw.read_bytes(), execution)
    if args.out.exists():
        raise SystemExit("AUDIT_OUTPUT_ALREADY_EXISTS")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["errors"], "raw_sha256": result.get("raw_sha256")}, sort_keys=True))
    return 0 if result["status"] == "PASS_TYPED_MARGIN_CONTRACT_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
