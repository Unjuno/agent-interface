#!/usr/bin/env python3
"""Independent auditor for the frozen synthetic session-carbon ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _decimal(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise AuditError(f"invalid decimal: {label}") from None
    _require(result.is_finite(), f"non-finite decimal: {label}")
    return result


def _text(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f") if normalized else "0"


def _expected_rows(arm: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for activity in arm["activities"]:
        _require(activity["kind"] in {"attempt", "retry", "recovery"}, "unknown activity kind")
        for component in ("client", "provider"):
            amount = _decimal(activity[f"{component}_wh"], f"{activity['activity_id']}:{component}")
            _require(amount >= 0, "negative opportunity energy")
            rows.append(
                {
                    "row_id": f"{activity['activity_id']}:{component}",
                    "scope": "opportunity_work",
                    "activity_id": activity["activity_id"],
                    "opportunity_id": activity["opportunity_id"],
                    "kind": activity["kind"],
                    "component": component,
                    "boundary": "client_operational" if component == "client" else "provider_inference",
                    "energy_wh": str(activity[f"{component}_wh"]),
                }
            )
    for item in arm["session_energy"]:
        component = item["component"]
        _require(component in {"client", "provider"}, "unknown session-energy component")
        _require(item["kind"] in {"idle", "reserved_capacity"}, "unknown session overhead kind")
        amount = _decimal(item["wh"], item["row_id"])
        _require(amount >= 0, "negative session-overhead energy")
        rows.append(
            {
                "row_id": f"{item['row_id']}:{component}",
                "scope": "session_overhead",
                "activity_id": f"session-{item['row_id']}",
                "opportunity_id": None,
                "kind": item["kind"],
                "component": component,
                "boundary": "client_operational" if component == "client" else "provider_inference",
                "energy_wh": str(item["wh"]),
            }
        )
    ids = [row["row_id"] for row in rows]
    _require(len(ids) == len(set(ids)), "duplicate expected energy row identity")
    return rows


def _recompute(arm: dict[str, Any], raw_arm: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    opportunities = arm["opportunities"]
    states = {item["opportunity_id"]: item["state"] for item in opportunities}
    _require(len(states) == len(opportunities), "duplicate opportunity identity")
    _require(set(states.values()) <= {"verified_safe_effect", "failed", "skipped"}, "unknown opportunity state")
    activity_ids = [item["activity_id"] for item in arm["activities"]]
    _require(len(activity_ids) == len(set(activity_ids)), "duplicate activity identity")
    for activity in arm["activities"]:
        _require(activity["opportunity_id"] in states, "activity references unknown opportunity")
        _require(states[activity["opportunity_id"]] != "skipped", "skipped opportunity has work activity")
        _require(activity["outcome"] in {"success", "failure", "recovered_without_effect"}, "unknown activity outcome")
    rows = raw_arm["energy_rows"]
    row_ids = [row.get("row_id") for row in rows]
    _require(len(row_ids) == len(set(row_ids)), "duplicate energy row identity")
    _require(rows == _expected_rows(arm), "energy rows omitted, duplicated, relabeled, or inconsistent with frozen source")

    totals = {"client": Decimal(0), "provider": Decimal(0)}
    for row in rows:
        _require(row["component"] in totals, "unknown component boundary")
        totals[row["component"]] += _decimal(row["energy_wh"], row["row_id"])
    safe_count = sum(state == "verified_safe_effect" for state in states.values())
    _require(safe_count > 0, "zero verified-effect denominator")
    total_wh = totals["client"] + totals["provider"]
    factor = raw["carbon_intensity"]
    central_factor = _decimal(factor["central_g_co2e_per_kwh"], "central grid intensity")
    low_factor = _decimal(factor["low_g_co2e_per_kwh"], "low grid intensity")
    high_factor = _decimal(factor["high_g_co2e_per_kwh"], "high grid intensity")
    _require(Decimal(0) <= low_factor <= central_factor <= high_factor, "invalid grid intensity bounds")
    operational = {
        "central": total_wh * central_factor / Decimal(1000),
        "low": total_wh * low_factor / Decimal(1000),
        "high": total_wh * high_factor / Decimal(1000),
    }
    embodied = {
        bound: sum(
            _decimal(value[bound + "_g_co2e"], f"embodied {component} {bound}")
            for component, value in raw["embodied_allocation"]["components"].items()
        )
        for bound in ("central", "low", "high")
    }
    _require(all(embodied["low"] <= embodied[key] <= embodied["high"] for key in ("central",)), "invalid embodied bounds")
    metrics = {
        "offered_opportunities": len(opportunities),
        "started_opportunities": sum(state != "skipped" for state in states.values()),
        "safe_verified_effects": safe_count,
        "failed_opportunities": sum(state == "failed" for state in states.values()),
        "skipped_opportunities": sum(state == "skipped" for state in states.values()),
        "activity_counts": {
            kind: sum(item["kind"] == kind for item in arm["activities"])
            for kind in ("attempt", "retry", "recovery")
        },
        "client_energy_wh": _text(totals["client"]),
        "provider_energy_wh": _text(totals["provider"]),
        "total_energy_wh": _text(total_wh),
        "client_joules_per_safe_effect": _text(totals["client"] * Decimal(3600) / safe_count),
        "operational_co2e_g": {key: _text(value) for key, value in operational.items()},
        "operational_co2e_per_safe_effect_g": {
            key: _text(value / safe_count) for key, value in operational.items()
        },
        "embodied_allocated_co2e_g": {key: _text(value) for key, value in embodied.items()},
        "embodied_allocated_co2e_per_safe_effect_g": {
            key: _text(value / safe_count) for key, value in embodied.items()
        },
    }
    _require(raw_arm["reported"] == metrics, "reported arm metrics disagree with independent recomputation")
    return metrics


def _contrast(reference: dict[str, Any], alternate: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    delta_energy = Decimal(alternate["total_energy_wh"]) - Decimal(reference["total_energy_wh"])
    grid = raw["carbon_intensity"]
    low = delta_energy * _decimal(grid["low_g_co2e_per_kwh"], "low grid intensity") / Decimal(1000)
    high = delta_energy * _decimal(grid["high_g_co2e_per_kwh"], "high grid intensity") / Decimal(1000)
    alternate_effects = alternate["safe_verified_effects"]
    reference_effects = reference["safe_verified_effects"]
    client_delta = Decimal(alternate["client_joules_per_safe_effect"]) - Decimal(
        reference["client_joules_per_safe_effect"]
    )
    central_delta = Decimal(alternate["operational_co2e_g"]["central"]) - Decimal(
        reference["operational_co2e_g"]["central"]
    )
    return {
        "safe_verified_effects_delta": alternate_effects - reference_effects,
        "client_joules_per_safe_effect_delta": _text(client_delta),
        "session_operational_co2e_g": {
            "delta_central": _text(central_delta),
            "delta_low": _text(min(low, high)),
            "delta_high": _text(max(low, high)),
        },
    }


def audit_raw(
    source: dict[str, Any],
    raw: dict[str, Any],
    expected_source_sha256: str,
    source_bytes: bytes,
) -> dict[str, Any]:
    _require(hashlib.sha256(source_bytes).hexdigest() == expected_source_sha256, "frozen source hash mismatch")
    _require(json.loads(source_bytes) == source, "parsed source differs from frozen source bytes")
    _require(raw.get("source_sha256") == expected_source_sha256, "source hash mismatch")
    _require(len(expected_source_sha256) == 64, "invalid expected source hash")
    _require(raw.get("schema_version") == "system-carbon-rebound-t0-raw-v1", "wrong raw schema")
    for key in ("claim_boundary", "session_minutes", "carbon_intensity", "embodied_allocation"):
        _require(raw.get(key) == source.get(key), f"frozen input mismatch: {key}")
    _require(raw.get("claim_boundary", "").startswith("synthetic accounting-method validation only"), "measurement claim exceeds T0 boundary")
    _require(raw.get("session_minutes") == 60, "session budget mismatch")
    expected_case_ids = [case["case_id"] for case in source["cases"]]
    _require(set(raw.get("cases", {})) == set(expected_case_ids), "case set mismatch")
    results: dict[str, Any] = {}
    for case in source["cases"]:
        case_id = case["case_id"]
        raw_case = raw["cases"][case_id]
        expected_arm_ids = [arm["arm_id"] for arm in case["arms"]]
        _require(set(raw_case) == set(expected_arm_ids) | {"contrast"}, f"arm set mismatch: {case_id}")
        computed: dict[str, Any] = {}
        for source_arm in case["arms"]:
            arm_id = source_arm["arm_id"]
            raw_arm = raw_case[arm_id]
            _require(raw_arm.get("opportunities") == source_arm["opportunities"], f"opportunity ledger mismatch: {case_id}/{arm_id}")
            _require(raw_arm.get("activities") == source_arm["activities"], f"activity ledger mismatch: {case_id}/{arm_id}")
            computed[arm_id] = _recompute(source_arm, raw_arm, raw)
        expected_contrast = _contrast(computed["reference"], computed["alternate"], raw)
        _require(raw_case.get("contrast") == expected_contrast, f"paired contrast mismatch: {case_id}")
        results[case_id] = {"arms": computed, "contrast": expected_contrast}

    no_demand = results["no_demand_change"]
    _require(no_demand["contrast"]["safe_verified_effects_delta"] == 0, "no-demand control changed safe-effect count")
    _require(no_demand["contrast"]["session_operational_co2e_g"]["delta_central"] == "0", "no-demand control should have equal central session emissions")
    expansion = results["beneficial_expansion"]
    _require(expansion["contrast"]["safe_verified_effects_delta"] > 0, "expansion control failed to increase safe effects")
    _require(Decimal(expansion["contrast"]["session_operational_co2e_g"]["delta_central"]) < 0, "beneficial expansion did not reduce session emissions")
    reversal = results["seeded_sign_reversal"]
    _require(Decimal(reversal["contrast"]["client_joules_per_safe_effect_delta"]) < 0, "sign-reversal control did not reduce client energy per effect")
    _require(Decimal(reversal["contrast"]["session_operational_co2e_g"]["delta_low"]) > 0, "sign-reversal lower bound is not positive")
    return {
        "status": "PASS_METHOD_SCOPED",
        "source_sha256": expected_source_sha256,
        "claim_boundary": "synthetic accounting method only; no empirical environmental, GUI, model, or product result",
        "formulas": {
            "operational_co2e_g": "sum(component_energy_wh) * grid_g_co2e_per_kwh / 1000",
            "client_joules_per_safe_effect": "sum(client_component_wh including idle) * 3600 / independently_verified_safe_effect_count",
            "embodied_co2e_per_safe_effect": "declared session allocation bounds / independently_verified_safe_effect_count; separate from operational carbon",
            "paired_delta_bounds": "shared frozen grid-factor interval applied to alternate-minus-reference Wh; endpoint order reversed for negative deltas",
        },
        "uncertainty_kind": source["carbon_intensity"]["uncertainty_kind"],
        "cases": results,
        "model_calls": 0,
        "device_measurements": 0,
        "provider_measurements": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    raw = json.loads(args.raw.read_bytes())
    source = json.loads(source_bytes)
    report = audit_raw(source, raw, hashlib.sha256(source_bytes).hexdigest(), source_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_METHOD_SCOPED: 3 cases independently reconciled; 0 model/device/provider measurements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
