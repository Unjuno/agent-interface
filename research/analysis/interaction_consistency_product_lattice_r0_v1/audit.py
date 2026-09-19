from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

LEVEL = {"SERIAL": 0, "PHASE_OVERLAP": 1, "FULL_PARALLEL": 2}


def canonical_sha(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def independent_oracle(row):
    base_ok = (
        bool(row["readset_complete"])
        and bool(row["readset_current"])
        and bool(row["global_conflict_free"])
        and bool(row["effects_commute"])
    )
    if not base_ok:
        return "SERIAL"
    if bool(row["simultaneous_input_requested"]):
        return "FULL_PARALLEL" if bool(row["actuator_independent"]) else "SERIAL"
    return "PHASE_OVERLAP"


def audit_objects(rows, result):
    errors = []
    if len(rows) != 128:
        errors.append(f"state_count:{len(rows)}")
    if result.get("state_count") != len(rows):
        errors.append("summary_state_count")
    if result.get("rows_sha256") != canonical_sha(rows):
        errors.append("rows_sha256")

    product_mismatch = 0
    surface_not_readset = []
    readset_not_surface = []
    policy = {name: {"unsafe": 0, "false_serial": 0, "missed_full": 0, "decision_counts": {k: 0 for k in LEVEL}}
              for name in ["SAFE_SERIAL", "SURFACE_ONLY", "READSET_ONLY", "ACTUATOR_ONLY", "STRICT_FULL_ONLY", "PRODUCT"]}
    phase_shared = 0
    full_ind = 0

    seen = set()
    for row in rows:
        bits = tuple(bool(row[k]) for k in [
            "surface_disjoint", "readset_complete", "readset_current", "global_conflict_free",
            "effects_commute", "actuator_independent", "simultaneous_input_requested"
        ])
        if bits in seen:
            errors.append("duplicate_state")
        seen.add(bits)

        truth = independent_oracle(row)
        if row.get("oracle") != truth:
            errors.append(f"oracle_row:{row.get('index')}")
        product = row.get("decisions", {}).get("PRODUCT")
        if product != truth:
            product_mismatch += 1

        rs = bool(row["surface_disjoint"])
        rr = bool(row["readset_complete"]) and bool(row["readset_current"])
        if rs and not rr:
            surface_not_readset.append(row["index"])
        if rr and not rs:
            readset_not_surface.append(row["index"])

        if truth == "PHASE_OVERLAP" and not bool(row["actuator_independent"]):
            phase_shared += 1
        if truth == "FULL_PARALLEL" and bool(row["actuator_independent"]):
            full_ind += 1

        for name in policy:
            dec = row.get("decisions", {}).get(name)
            if dec not in LEVEL:
                errors.append(f"decision:{name}:{row.get('index')}")
                continue
            policy[name]["decision_counts"][dec] += 1
            policy[name]["unsafe"] += int(LEVEL[dec] > LEVEL[truth])
            policy[name]["false_serial"] += int(dec == "SERIAL" and truth != "SERIAL")
            policy[name]["missed_full"] += int(dec != "FULL_PARALLEL" and truth == "FULL_PARALLEL")

    checks = {
        "product_oracle_mismatch": product_mismatch,
        "surface_not_readset_count": len(surface_not_readset),
        "readset_not_surface_count": len(readset_not_surface),
        "phase_overlap_shared_actuator_count": phase_shared,
        "full_parallel_independent_actuator_count": full_ind,
        "policy_counts": policy,
    }
    for k, v in checks.items():
        if result.get(k) != v:
            errors.append(f"summary:{k}")

    pass_expected = (
        product_mismatch == 0
        and bool(surface_not_readset)
        and bool(readset_not_surface)
        and policy["SURFACE_ONLY"]["unsafe"] > 0
        and policy["READSET_ONLY"]["unsafe"] > 0
        and policy["ACTUATOR_ONLY"]["unsafe"] > 0
        and policy["SAFE_SERIAL"]["unsafe"] == 0
        and policy["SAFE_SERIAL"]["false_serial"] > 0
        and phase_shared > 0
        and full_ind > 0
    )
    expected_decision = "PASS_CONSISTENCY_PRODUCT_NOT_SCALAR_SCOPED" if pass_expected else "HOLD_OR_FAIL"
    if result.get("decision") != expected_decision:
        errors.append("summary:decision")
    return errors


def corruption_controls(rows, result):
    outcomes = {}

    r1 = copy.deepcopy(rows)
    r1[0]["decisions"]["PRODUCT"] = "FULL_PARALLEL"
    outcomes["product_row_mutation_detected"] = bool(audit_objects(r1, result))

    r2 = copy.deepcopy(rows)
    r2[-1]["oracle"] = "SERIAL" if r2[-1]["oracle"] != "SERIAL" else "FULL_PARALLEL"
    outcomes["oracle_row_mutation_detected"] = bool(audit_objects(r2, result))

    s3 = copy.deepcopy(result)
    s3["product_oracle_mismatch"] = int(s3["product_oracle_mismatch"]) + 1
    outcomes["summary_mutation_detected"] = bool(audit_objects(rows, s3))

    return outcomes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    root = Path(args.root)
    rows = json.loads((root / "ROWS.json").read_text(encoding="utf-8"))
    result = json.loads((root / "RESULT.json").read_text(encoding="utf-8"))
    errors = audit_objects(rows, result)
    corrupt = corruption_controls(rows, result)
    out = {"errors": errors, "corruption_controls": corrupt, "pass": (not errors and all(corrupt.values()))}
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if out["pass"] else 3)


if __name__ == "__main__":
    main()
