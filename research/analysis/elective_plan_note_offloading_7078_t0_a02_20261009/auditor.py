#!/usr/bin/env python3
"""Independent contract and loss auditor; no candidate imports."""
import json
import sys
from pathlib import Path


def audit(data, output, oracle):
    errors = []
    mandatory = data.get("mandatory", [])
    mandatory_ids = [r.get("id") for r in mandatory]
    if mandatory_ids != oracle["mandatory_ids"] or any(r.get("role") != "mandatory_unresolved_effect" for r in mandatory):
        errors.append("mandatory ledger role or identity changed")
    if set(data["calibration_ids"]) & set(data["held_out_ids"]):
        errors.append("calibration/test leakage")
    if output.get("calibration_ids") != data["calibration_ids"] or output.get("held_out_ids") != data["held_out_ids"]:
        errors.append("split provenance changed")
    by_id = {r.get("id"): r for r in output.get("rows", [])}
    if set(by_id) != {c["id"] for c in data["cases"]}:
        errors.append("case set mismatch")
    for case in data["cases"]:
        row = by_id.get(case["id"], {})
        q0, q1, loss = case["q0"], case["q1"], case["safe_rediscovery_loss"]
        d, cost = case["delivery_probability"], case["forecast_write_read_cost"]
        no_note = (1 - q0) * loss
        note = cost + d * (1 - q1) * loss + (1 - d) * (1 - q0) * loss
        eligible = (case["delivered"] and bool(case["source"]) and case["source"] == case["note_source"]
                    and case["generation"] == 9 and case["q0_kind"] == "future_unaided_forecast")
        expected = "NOTE" if eligible and note < no_note else "NO_NOTE"
        if row.get("choice") != expected or expected != oracle["expected_choices"].get(case["id"]):
            errors.append(f"decision mismatch: {case['id']}")
        if row.get("no_note_loss") != no_note or row.get("note_loss") != note:
            errors.append(f"loss mismatch or omitted cost: {case['id']}")
        if row.get("mandatory_ids") != mandatory_ids:
            errors.append(f"mandatory record not conserved: {case['id']}")
        if not case["delivered"] and row.get("choice") == "NOTE":
            errors.append(f"undelivered note used: {case['id']}")
        if case["generation"] != 9 and row.get("choice") == "NOTE":
            errors.append(f"stale generation used: {case['id']}")
        if case["source"] != case["note_source"] and row.get("choice") == "NOTE":
            errors.append(f"source binding mismatch: {case['id']}")
        if case["q0_kind"] != "future_unaided_forecast" and row.get("choice") == "NOTE":
            errors.append(f"present support substituted for q0: {case['id']}")
    return errors


if __name__ == "__main__":
    base = Path(sys.argv[1])
    data = json.loads((base / "input.json").read_text())
    output = json.loads(Path(sys.argv[2]).read_text())
    oracle = json.loads((base / "oracle.json").read_text())
    errors = audit(data, output, oracle)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True))
    raise SystemExit(bool(errors))
