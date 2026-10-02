#!/usr/bin/env python3
"""Independent raw-only auditor; deliberately does not import candidate code."""

import json
import sys
from collections import Counter
from pathlib import Path


def average(xs):
    return sum(xs) / len(xs) if xs else None


def audit_rows(rows, equal_effect=False):
    ids = [r["row_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate row_id")
    actual_schedule = Counter((r["a_on"], r["b_on"], r["a_version"], r["b_version"])
                             for r in rows if r["attempt_status"] == "OBSERVED"
                             and r["a_version"] in ("a1", "a2"))
    expected_schedule = Counter()
    for a_on in (0, 1):
        for b_on in (0, 1):
            aversions = (("a1", 1), ("a2", 1)) if not a_on else (("a1", 8), ("a2", 2))
            bversions = (("b1", 1), ("b2", 1)) if b_on else (("b1", 1),)
            for av, an in aversions:
                for bv, bn in bversions:
                    if a_on and b_on and av == "a2" and bv == "b2":
                        continue
                    expected_schedule[(a_on, b_on, av, bv)] = an * bn
    if actual_schedule != expected_schedule:
        raise ValueError("raw rows differ from frozen coalition/version assignment schedule")
    unresolved = {r["row_id"]: r["attempt_status"] for r in rows if r["row_id"] in
                  ("unknown-version", "missing-attempt", "structural-zero")}
    if unresolved != {"unknown-version": "OBSERVED", "missing-attempt": "FAILED_NO_OUTCOME",
                      "structural-zero": "NOT_ASSIGNED"}:
        raise ValueError("unknown, failed, or structural-zero receipt missing/altered")
    for row in rows:
        if row["attempt_status"] == "NOT_ASSIGNED":
            if row["feasible"] or row["task_effect"] is not None:
                raise ValueError("structural-zero cell imputed or marked feasible")
        elif row["attempt_status"] == "FAILED_NO_OUTCOME":
            if row["task_effect"] is not None or row["safety_event"] is not None:
                raise ValueError("failed attempt fabricated an outcome")
        elif row["a_version"] == "UNKNOWN":
            if row["task_effect"] is not None or row["safety_event"] is not None:
                raise ValueError("unknown version assigned a usable outcome")
        elif row["attempt_status"] == "OBSERVED":
            if row["task_effect"] is None or row["safety_event"] is None:
                raise ValueError("observed outcome incomplete")
            if row["a_on"] and row["a_version"] == "a2" and row["b_on"] and row["b_version"] == "b2":
                raise ValueError("observed structural-zero combination")
            b_increment = (3 if row["b_version"] == "b1" else 5) * row["b_on"]
            a_increment = (5 if equal_effect else (2 if row["a_version"] == "a1" else 8))
            expected_effect = 10 + a_increment * row["a_on"] + b_increment
            if row["task_effect"] != expected_effect:
                raise ValueError("task-effect cell disagrees with frozen case potential outcomes")
            if row["safety_event"] != int(row["a_on"] and row["a_version"] == "a2"):
                raise ValueError("safety outcome changed or was scalarized")
        else:
            raise ValueError("unrecognized status")

    observed = [r for r in rows if r["attempt_status"] == "OBSERVED" and r["feasible"]
                and r["a_version"] in ("a1", "a2")]
    estimates = {}
    for b in (0, 1):
        control = [r for r in observed if r["b_on"] == b and r["a_on"] == 0]
        treated = [r for r in observed if r["b_on"] == b and r["a_on"] == 1]
        if not control or not treated:
            estimates[str(b)] = {"pooled": None, "standardized": "UNKNOWN"}
            continue
        pooled = average([r["task_effect"] for r in treated]) - average([r["task_effect"] for r in control])
        cells0 = {(r["a_version"], r["b_version"]): r["task_effect"] for r in control}
        cells1 = {(r["a_version"], r["b_version"]): r["task_effect"] for r in treated}
        support = sorted(set(cells0) & set(cells1))
        standardized = (sum(cells1[c] - cells0[c] for c in support) / len(support)
                        if support else "UNKNOWN")
        estimates[str(b)] = {"pooled": pooled, "standardized": standardized,
                              "common_version_cells": [list(c) for c in support]}
    return estimates


def main(raw_path, candidate_path, out_path):
    raw = json.loads(Path(raw_path).read_text())
    candidate = json.loads(Path(candidate_path).read_text())
    errors = []
    audited = {}
    for name, case in raw.items():
        estimates = audit_rows(case["raw_rows"], equal_effect=(name == "equal_effect"))
        audited[name] = estimates
        candidate_case = candidate.get("cases", {}).get(name, {})
        if estimates != candidate_case.get("estimates"):
            errors.append(f"{name}: candidate calculation mismatch")
        if candidate_case.get("raw_rows") != case["raw_rows"]:
            errors.append(f"{name}: candidate/raw record mismatch")
    equal = audited["equal_effect"]
    variant = audited["version_interaction"]
    if equal["0"]["pooled"] != equal["0"]["standardized"]:
        errors.append("equal-effect negative control did not agree")
    if variant["0"]["pooled"] == variant["0"]["standardized"]:
        errors.append("version-mixture challenge did not separate pooled and common-mixture effects")
    if ["a2", "b2"] in variant["1"]["common_version_cells"]:
        errors.append("infeasible cell was included in standardized support")
    safety_counter = Counter((case_name, r["safety_event"]) for case_name, case in raw.items()
                             for r in case["raw_rows"] if r["attempt_status"] == "OBSERVED"
                             and r["safety_event"] is not None)
    # Safety is only counted as its own raw column; it is never combined with task_effect.
    if not safety_counter:
        errors.append("missing independent safety outcomes")
    report = {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "independent_estimands": audited,
              "safety_event_counts_separate": [{"case": k[0], "safety_event": k[1], "count": v}
                                                for k, v in sorted(safety_counter.items())],
              "unknown_version_present": any(r["a_version"] == "UNKNOWN" for c in raw.values() for r in c["raw_rows"]),
              "failed_attempt_present": any(r["attempt_status"] == "FAILED_NO_OUTCOME" for c in raw.values() for r in c["raw_rows"]),
              "structural_zero_present": any(not r["feasible"] for c in raw.values() for r in c["raw_rows"]),
              "candidate_schema": candidate.get("schema"), "errors": errors}
    Path(out_path).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": report["disposition"], "errors": errors,
                      "estimands": audited}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
