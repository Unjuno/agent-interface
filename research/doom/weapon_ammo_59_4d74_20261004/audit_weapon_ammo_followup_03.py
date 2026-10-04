"""Third follow-up audit for the retained selected-weapon/ammo fixture."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

from audit_weapon_ammo_followup_02 import audit as audit_followup_02, finite_number, read_jsonl


def audit(root: Path) -> dict[str, Any]:
    report = audit_followup_02(root)
    cell = root / "00-coast"
    if not cell.is_dir():
        cell = root / "sample-pair-04" / "00-coast"
    events = read_jsonl(cell / "events.jsonl")
    rows = read_jsonl(cell / "scorer-last-action.jsonl")
    initial = next(
        row for row in events
        if row.get("event") == "typed_observation" and row.get("id") == "initial"
    )
    candidates = [row for row in rows if row.get("coherent_tic")]
    near = min(
        candidates,
        key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
    )
    variables = near.get("variables")
    coherent = (
        type(near.get("coherent_tic")) is bool
        and near["coherent_tic"] is True
        and type(near.get("sample_started_ns")) is int
        and type(near.get("sample_returned_ns")) is int
        and near["sample_started_ns"] <= near["sample_returned_ns"]
        and type(near.get("tic_before")) is int
        and type(near.get("tic_after")) is int
        and near["tic_before"] == near["tic_after"]
        and isinstance(variables, dict)
        and all(finite_number(value) for value in variables.values())
    )
    checks = report.setdefault("checks", {})
    checks["nearest_api_sample_coherent"] = coherent
    if not coherent and report.get("disposition") == "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED":
        report["disposition"] = "HOLD_AUDIT_CHECK_FAILED"
    report["nearest_api_sample_coherence_contract"] = (
        "nearest comparison row must carry exact true coherence, ordered integer "
        "sample bounds, equal integer tic endpoints, and finite variables"
    )
    return report


def main() -> int:
    try:
        report = audit(Path(__file__).resolve().parent)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError, StopIteration) as exc:
        report = {"disposition": "HOLD_MALFORMED_OR_MISSING_EVIDENCE", "error": str(exc)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["disposition"] == "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main())
