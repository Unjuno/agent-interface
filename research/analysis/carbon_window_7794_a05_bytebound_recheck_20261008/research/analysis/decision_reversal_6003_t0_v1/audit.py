#!/usr/bin/env python3
"""Independent standard-library oracle; intentionally imports no selector code."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import platform
import sys
from pathlib import Path


def shannon(probabilities):
    value = 0.0
    for p in probabilities:
        if p > 0:
            value -= p * math.log2(p)
    return value


def independently_rank(spec):
    base = spec["baseline_actions"]
    mandatory_cost = spec["hard_sentinel"]["cost"]
    limit = spec["budget"]
    options = [item for item in spec["selector_fixture"]["experiments"]
               if item["cost"] + mandatory_cost <= limit]
    low_cost = sorted(options, key=lambda item: (item["cost"], item["id"]))[0]["id"]
    info = {}
    for item in options:
        probs = [entry["p"] for entry in item["outcomes"]["nominal"]]
        info[item["id"]] = shannon(probs)
    max_info = max(info.values())
    entropy_choice = sorted(name for name, score in info.items()
                            if abs(score - max_info) < 1e-12)[0]
    worst_case = {}
    for item in options:
        by_scenario = []
        for scenario, current_action in base.items():
            rows = item["outcomes"][scenario]
            mass = 0.0
            for row in rows:
                if row["next_action"] == "STOP":
                    continue
                if row["next_action"] != current_action:
                    mass += row["p"]
            by_scenario.append(mass)
        worst_case[item["id"]] = min(by_scenario)
    ceiling = max(worst_case.values()) if worst_case else 0.0
    if ceiling <= 1e-12:
        reversal_choice = "UNRANKABLE"
    else:
        candidates = [name for name, score in worst_case.items()
                      if abs(score - ceiling) < 1e-12]
        reversal_choice = sorted(candidates,
                                 key=lambda name: next(x["cost"] for x in options
                                                       if x["id"] == name))[0]
    return low_cost, entropy_choice, reversal_choice, info, worst_case


def set_null(spec):
    changed = copy.deepcopy(spec)
    for item in changed["selector_fixture"]["experiments"]:
        for scenario, action in changed["baseline_actions"].items():
            for row in item["outcomes"][scenario]:
                if row["next_action"] != "STOP":
                    row["next_action"] = action
    return changed


def validate(spec, result, freeze_digest, selector_digest):
    errors = []
    if spec.get("hard_sentinel", {}).get("mandatory") is not True:
        errors.append("mandatory sentinel missing")
    if spec["hard_sentinel"]["cost"] > spec["budget"]:
        errors.append("mandatory sentinel exceeds budget")
    expected_ids = {"A-cheap-irrelevant", "B-robust-reversal", "C-prior-sensitive"}
    items = spec["selector_fixture"]["experiments"]
    if {item["id"] for item in items} != expected_ids:
        errors.append("experiment set mismatch")
    action_set = set(spec["baseline_actions"].values()) | {"STOP"}
    for item in items:
        if item["cost"] <= 0 or item["cost"] + spec["hard_sentinel"]["cost"] > spec["budget"]:
            errors.append("infeasible experiment: " + item["id"])
        if set(item["outcomes"]) != set(spec["baseline_actions"]):
            errors.append("scenario set mismatch: " + item["id"])
        for scenario, rows in item["outcomes"].items():
            if abs(sum(row["p"] for row in rows) - 1.0) > 1e-12:
                errors.append("probability mass mismatch: " + item["id"] + "/" + scenario)
            if len({row["id"] for row in rows}) != len(rows):
                errors.append("duplicate outcome: " + item["id"] + "/" + scenario)
            for row in rows:
                if row["p"] < 0 or row["next_action"] not in action_set:
                    errors.append("invalid outcome: " + item["id"] + "/" + scenario)
                if row["id"].endswith("STOP") and row["next_action"] != "STOP":
                    errors.append("STOP mislabeled as support: " + item["id"] + "/" + scenario)
    cheap, entropy_choice, reversal_choice, info, robust = independently_rank(spec)
    observed = result.get("primary", {})
    if observed.get("cheapest") != cheap:
        errors.append("cheapest selector mismatch")
    if observed.get("nominal_entropy") != entropy_choice:
        errors.append("nominal entropy selector mismatch")
    if observed.get("robust_reversal") != reversal_choice:
        errors.append("robust selector mismatch")
    if observed.get("robust_scores") != robust:
        errors.append("robust scores mismatch")
    if result.get("freeze_sha256") != freeze_digest:
        errors.append("freeze digest mismatch")
    if result.get("selector_sha256") != selector_digest:
        errors.append("candidate source digest mismatch")
    if result.get("scientific_support_events") != 0:
        errors.append("synthetic fixture mislabeled as scientific support")
    if result.get("status") != "SYNTHETIC_CONSTRUCTION_ONLY":
        errors.append("scope/status mismatch")
    ncheap, nentropy, nreversal, _, nrobust = independently_rank(set_null(spec))
    if nreversal != "UNRANKABLE" or max(nrobust.values()) != 0.0:
        errors.append("null control manufactures decision value")
    # The prior-sensitivity control must actually reverse B/C's entropy ranking.
    if not (info["C-prior-sensitive"] > info["B-robust-reversal"]):
        errors.append("nominal B/C entropy order not as frozen")
    shifted = {item["id"]: shannon([row["p"] for row in item["outcomes"]["capture_lean"]])
               for item in items}
    if not (shifted["B-robust-reversal"] > shifted["C-prior-sensitive"]):
        errors.append("prior-range B/C entropy order did not reverse")
    if result.get("null_control", {}).get("robust_reversal") != "UNRANKABLE":
        errors.append("candidate failed null UNRANKABLE control")
    return errors


def main():
    folder = Path(__file__).resolve().parent
    freeze_path = folder / "FREEZE.json"
    result_path = folder / "candidate_result.json"
    candidate_path = folder / "select.py"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(
        freeze, result, hashlib.sha256(freeze_bytes).hexdigest(),
        hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    )
    report = {
        "status": "PASS_HOST_ONLY_CONSTRUCTION" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze["main_sha"],
        "independent_oracle": "audit.py; no import from select.py",
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "primary": independently_rank(freeze)[:3],
        "scope": "does not satisfy the frozen disposable-container condition",
    }
    audit_path = folder / "independent_audit.json"
    audit_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
