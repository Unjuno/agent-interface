#!/usr/bin/env python3
"""Render the frozen synthetic accounting ledger without external measurements."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f") if normalized else "0"


def _energy_rows(arm: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for activity in arm["activities"]:
        for component in ("client", "provider"):
            rows.append(
                {
                    "row_id": f"{activity['activity_id']}:{component}",
                    "scope": "opportunity_work",
                    "activity_id": activity["activity_id"],
                    "opportunity_id": activity["opportunity_id"],
                    "kind": activity["kind"],
                    "component": component,
                    "boundary": "client_operational" if component == "client" else "provider_inference",
                    "energy_wh": activity[f"{component}_wh"],
                }
            )
    for item in arm["session_energy"]:
        component = item["component"]
        rows.append(
            {
                "row_id": f"{item['row_id']}:{component}",
                "scope": "session_overhead",
                "activity_id": f"session-{item['row_id']}",
                "opportunity_id": None,
                "kind": item["kind"],
                "component": component,
                "boundary": "client_operational" if component == "client" else "provider_inference",
                "energy_wh": item["wh"],
            }
        )
    return rows


def _summarize_arm(arm: dict[str, Any], rows: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    energy = {"client": Decimal(0), "provider": Decimal(0)}
    for row in rows:
        energy[row["component"]] += Decimal(row["energy_wh"])

    safe = sum(item["state"] == "verified_safe_effect" for item in arm["opportunities"])
    offered = len(arm["opportunities"])
    started = sum(item["state"] != "skipped" for item in arm["opportunities"])
    failed = sum(item["state"] == "failed" for item in arm["opportunities"])
    skipped = sum(item["state"] == "skipped" for item in arm["opportunities"])
    activity_counts = {
        kind: sum(item["kind"] == kind for item in arm["activities"])
        for kind in ("attempt", "retry", "recovery")
    }
    total_wh = energy["client"] + energy["provider"]
    factor = source["carbon_intensity"]
    op = {
        key: total_wh * Decimal(factor[field]) / Decimal(1000)
        for key, field in (
            ("central", "central_g_co2e_per_kwh"),
            ("low", "low_g_co2e_per_kwh"),
            ("high", "high_g_co2e_per_kwh"),
        )
    }
    embodied = {
        bound: sum(
            Decimal(item[bound + "_g_co2e"])
            for item in source["embodied_allocation"]["components"].values()
        )
        for bound in ("central", "low", "high")
    }
    return {
        "offered_opportunities": offered,
        "started_opportunities": started,
        "safe_verified_effects": safe,
        "failed_opportunities": failed,
        "skipped_opportunities": skipped,
        "activity_counts": activity_counts,
        "client_energy_wh": _decimal_text(energy["client"]),
        "provider_energy_wh": _decimal_text(energy["provider"]),
        "total_energy_wh": _decimal_text(total_wh),
        "client_joules_per_safe_effect": _decimal_text(energy["client"] * 3600 / safe),
        "operational_co2e_g": {key: _decimal_text(value) for key, value in op.items()},
        "operational_co2e_per_safe_effect_g": {
            key: _decimal_text(value / safe) for key, value in op.items()
        },
        "embodied_allocated_co2e_g": {key: _decimal_text(value) for key, value in embodied.items()},
        "embodied_allocated_co2e_per_safe_effect_g": {
            key: _decimal_text(value / safe) for key, value in embodied.items()
        },
    }


def _contrast(reference: dict[str, Any], alternate: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    ref_wh = Decimal(reference["reported"]["total_energy_wh"])
    alt_wh = Decimal(alternate["reported"]["total_energy_wh"])
    delta_wh = alt_wh - ref_wh
    factor = source["carbon_intensity"]
    bounds = [
        delta_wh * Decimal(factor["low_g_co2e_per_kwh"]) / Decimal(1000),
        delta_wh * Decimal(factor["high_g_co2e_per_kwh"]) / Decimal(1000),
    ]
    return {
        "safe_verified_effects_delta": (
            alternate["reported"]["safe_verified_effects"]
            - reference["reported"]["safe_verified_effects"]
        ),
        "client_joules_per_safe_effect_delta": _decimal_text(
            Decimal(alternate["reported"]["client_joules_per_safe_effect"])
            - Decimal(reference["reported"]["client_joules_per_safe_effect"])
        ),
        "session_operational_co2e_g": {
            "delta_central": _decimal_text(
                Decimal(alternate["reported"]["operational_co2e_g"]["central"])
                - Decimal(reference["reported"]["operational_co2e_g"]["central"])
            ),
            "delta_low": _decimal_text(min(bounds)),
            "delta_high": _decimal_text(max(bounds)),
        },
    }


def build_raw(source: dict[str, Any], source_sha256: str) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "schema_version": "system-carbon-rebound-t0-raw-v1",
        "source_sha256": source_sha256,
        "claim_boundary": source["claim_boundary"],
        "session_minutes": source["session_minutes"],
        "carbon_intensity": copy.deepcopy(source["carbon_intensity"]),
        "embodied_allocation": copy.deepcopy(source["embodied_allocation"]),
        "cases": {},
    }
    for case in source["cases"]:
        rendered_arms: dict[str, Any] = {}
        for source_arm in case["arms"]:
            arm = {
                "opportunities": copy.deepcopy(source_arm["opportunities"]),
                "activities": copy.deepcopy(source_arm["activities"]),
                "energy_rows": _energy_rows(source_arm),
            }
            arm["reported"] = _summarize_arm(arm, arm["energy_rows"], source)
            rendered_arms[source_arm["arm_id"]] = arm
        rendered_arms["contrast"] = _contrast(
            rendered_arms["reference"], rendered_arms["alternate"], source
        )
        raw["cases"][case["case_id"]] = rendered_arms
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source = json.loads(source_bytes)
    raw = build_raw(source, hashlib.sha256(source_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("candidate completed: 3 synthetic cases; no model/device/provider calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
