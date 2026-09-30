"""Independent raw-only audit. Does not import candidate model or runner."""
import json
import sys
from fractions import Fraction
from pathlib import Path

import oracle


def audit(raw: dict) -> list[str]:
    errors = []
    if raw.get("source_main") != "4439161abd6f8ccf276babc1c39c43428394e773":
        errors.append("SOURCE_MAIN_MISMATCH")
    rows = raw.get("rows", [])
    expected_keys = {(c, p) for c in (
        "certain_safe", "rare_hazard", "near_budget", "dangerous_minority",
        "ambiguous", "mostly_unsafe", "misspecified_hazard") for p in
        ("MAP", "WORST_CASE", "RISK_BUDGET", "EXPECTED_UTILITY")}
    seen = set()
    for row in rows:
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append(f"DUPLICATE_ROW:{key}")
        seen.add(key)
        reported, actual = Fraction(row["reported"]), Fraction(row["actual"])
        if row.get("admitted") != oracle.oracle_decision(key[1], reported):
            errors.append(f"DECISION_MISMATCH:{key}")
        if row.get("branches") != oracle.branch_masses(actual):
            errors.append(f"BRANCH_MASS_MISMATCH:{key}")
        utility = oracle.expected_utility(reported)
        utility_text = f"{utility.numerator}/{utility.denominator}" if row.get("admitted") else "0/1"
        if row.get("model_expected_utility_if_admitted") != utility_text:
            errors.append(f"UTILITY_MISMATCH:{key}")
        if row.get("misspecification_exposed") != (actual != reported):
            errors.append(f"MISSPECIFICATION_HIDDEN:{key}")
        unsafe = actual if row.get("admitted") else Fraction(0)
        unsafe_text = f"{unsafe.numerator}/{unsafe.denominator}"
        if row.get("actual_unsafe_mass_if_admitted") != unsafe_text:
            errors.append(f"ACTUAL_RISK_MISMATCH:{key}")
        if row.get("authority") is not False or row.get("effect") is not False:
            errors.append(f"AUTHORITY_OR_EFFECT:{key}")
    if seen != expected_keys:
        errors.append("ROW_SET_MISMATCH")
    # The risk contract is explicitly model-relative; the misspecified stress must violate
    # the true-risk bound visibly, never be reported as a guarantee.
    misspec = [r for r in rows if r["case_id"] == "misspecified_hazard" and r["policy"] == "RISK_BUDGET"]
    if len(misspec) != 1 or not misspec[0]["admitted"] or not misspec[0]["misspecification_exposed"] or Fraction(misspec[0]["actual_unsafe_mass_if_admitted"]) <= Fraction(1, 20):
        errors.append("MISSPECIFICATION_CONTROL_NOT_EXPOSED")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 -B audit.py RAW.json AUDIT.json")
    source, destination = map(Path, sys.argv[1:])
    result = {"status": "PASS_READONLY", "errors": audit(json.loads(source.read_text(encoding="utf-8")))}
    if result["errors"]:
        result["status"] = "FAIL_READONLY"
    if destination.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)
