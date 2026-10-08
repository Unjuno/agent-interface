#!/usr/bin/env python3
"""Deterministic candidate renderer for Issue #5707 typed-margin T0."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def classify_interval(margin: dict[str, Any]) -> str:
    if margin["status"] == "UNKNOWN":
        return "UNKNOWN"
    lo, hi, threshold = margin["lower"], margin["upper"], margin["threshold"]
    if not isinstance(lo, int) or isinstance(lo, bool):
        raise ValueError("MARGIN_LOWER_NOT_INTEGER")
    if not isinstance(hi, int) or isinstance(hi, bool):
        raise ValueError("MARGIN_UPPER_NOT_INTEGER")
    if lo > hi:
        raise ValueError("MARGIN_INTERVAL_REVERSED")
    if hi < threshold:
        return "CROSSED"
    if lo >= threshold:
        return "NOT_CROSSED"
    return "UNCERTAIN_INTERVAL_STRADDLES_THRESHOLD"


def build_ledger(plan: dict[str, Any]) -> list[dict[str, Any]]:
    opportunities = plan["opportunities"]
    ids = [item["opportunity_id"] for item in opportunities]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_OPPORTUNITY_ID")
    records: list[dict[str, Any]] = []
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)

    for item in opportunities:
        margin = item["margin"]
        rendered = None
        if margin is not None:
            rendered = dict(margin)
            rendered["classification"] = classify_interval(margin)
            key = (
                margin["purpose"], margin["boundary_kind"], margin["unit"],
                margin["contract_id"], margin["contract_version"], margin["threshold"],
            )
            groups[key].append({"id": item["opportunity_id"], "margin": rendered})
        records.append({
            "record_type": "opportunity",
            "allocation": plan["allocation"],
            "opportunity_id": item["opportunity_id"],
            "disposition": item["disposition"],
            "forbidden_effect": item["forbidden_effect"],
            "actuation_margin_status": item["actuation_margin_status"],
            "margin": rendered,
        })

    for key, entries in sorted(groups.items()):
        measured = [entry for entry in entries if entry["margin"]["status"] == "MEASURED"]
        lowers = [entry["margin"]["lower"] for entry in measured]
        uppers = [entry["margin"]["upper"] for entry in measured]
        records.append({
            "record_type": "typed_summary",
            "allocation": plan["allocation"],
            "purpose": key[0],
            "boundary_kind": key[1],
            "unit": key[2],
            "contract_id": key[3],
            "contract_version": key[4],
            "threshold": key[5],
            "opportunity_ids": sorted(entry["id"] for entry in entries),
            "observed_count": len(entries),
            "measured_count": len(measured),
            "unknown_count": sum(entry["margin"]["status"] == "UNKNOWN" for entry in entries),
            "crossed_count": sum(entry["margin"]["classification"] == "CROSSED" for entry in entries),
            "not_crossed_count": sum(entry["margin"]["classification"] == "NOT_CROSSED" for entry in entries),
            "uncertain_count": sum(entry["margin"]["classification"] == "UNCERTAIN_INTERVAL_STRADDLES_THRESHOLD" for entry in entries),
            "minimum_interval": [min(lowers), min(uppers)] if measured else None,
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("OUTPUT_ALREADY_EXISTS")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    rows = build_ledger(plan)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"candidate": "COMPLETE", "rows": len(rows), "opportunities": len(plan["opportunities"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
