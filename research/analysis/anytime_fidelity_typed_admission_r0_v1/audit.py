from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROLE_CURRENT = "CURRENT"
ROLE_TEMPORAL = "TEMPORAL"
ROLE_VERIFY = "VERIFY"
EXPECTED_CATALOG = [
    {"name": "CURRENT", "cost": 1, "evidence": ["CURRENT"], "rank": 0},
    {"name": "TEMPORAL", "cost": 3, "evidence": ["CURRENT", "TEMPORAL"], "rank": 1},
    {"name": "VERIFY", "cost": 3, "evidence": ["CURRENT", "VERIFY"], "rank": 2},
    {"name": "FULL", "cost": 6, "evidence": ["CURRENT", "TEMPORAL", "VERIFY"], "rank": 3},
]
EXPECTED_BY_NAME = {x["name"]: x for x in EXPECTED_CATALOG}
POLICIES = [
    "SCALAR_RAW_HIGHEST",
    "SCALAR_RESERVED_HIGHEST",
    "SCALAR_RESERVED_POSTCHECK",
    "CURRENT_ONLY",
    "TYPED_RESERVED",
]
SOURCE_FILES = ["PLAN.md", "candidate.py", "formal.py", "audit.py"]


def canonical_sha(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_sets():
    roles = [ROLE_CURRENT, ROLE_TEMPORAL, ROLE_VERIFY]
    for bits in itertools.product([False, True], repeat=3):
        req = frozenset(r for r, keep in zip(roles, bits) if keep)
        if req:
            yield req


def variants():
    return [
        ("CURRENT", 1, frozenset({ROLE_CURRENT}), 0),
        ("TEMPORAL", 3, frozenset({ROLE_CURRENT, ROLE_TEMPORAL}), 1),
        ("VERIFY", 3, frozenset({ROLE_CURRENT, ROLE_VERIFY}), 2),
        ("FULL", 6, frozenset({ROLE_CURRENT, ROLE_TEMPORAL, ROLE_VERIFY}), 3),
    ]


def safe(slack, reserve, required, variant):
    _name, cost, evidence, _rank = variant
    return required.issubset(evidence) and cost + reserve <= slack


def feasible(slack, reserve, required):
    return any(safe(slack, reserve, required, v) for v in variants())


def select(policy, slack, reserve, required):
    vs = variants()
    by_name = {v[0]: v for v in vs}
    if policy == "SCALAR_RAW_HIGHEST":
        fit = [v for v in vs if v[1] <= slack]
        return max(fit, key=lambda v: v[3])[0] if fit else "DEFER"
    if policy == "SCALAR_RESERVED_HIGHEST":
        fit = [v for v in vs if v[1] + reserve <= slack]
        return max(fit, key=lambda v: v[3])[0] if fit else "DEFER"
    if policy == "SCALAR_RESERVED_POSTCHECK":
        fit = [v for v in vs if v[1] + reserve <= slack]
        if not fit:
            return "DEFER"
        chosen = max(fit, key=lambda v: v[3])
        return chosen[0] if required.issubset(chosen[2]) else "DEFER"
    if policy == "CURRENT_ONLY":
        v = by_name["CURRENT"]
        return "CURRENT" if safe(slack, reserve, required, v) else "DEFER"
    if policy == "TYPED_RESERVED":
        fit = [v for v in vs if safe(slack, reserve, required, v)]
        return max(fit, key=lambda v: (len(v[2]), v[3]))[0] if fit else "DEFER"
    raise ValueError(policy)


def classify(slack, reserve, required, chosen):
    exists = feasible(slack, reserve, required)
    if chosen == "DEFER":
        return {"deadline_violation": False, "evidence_violation": False, "unsafe": False, "false_defer": exists}
    v = {x[0]: x for x in variants()}[chosen]
    deadline = v[1] + reserve > slack
    evidence = not required.issubset(v[2])
    return {"deadline_violation": deadline, "evidence_violation": evidence, "unsafe": deadline or evidence, "false_defer": False}


def audit_objects(rows, result, source_root: Path | None, freeze):
    errors = []
    if result.get("catalog") != EXPECTED_CATALOG:
        errors.append("catalog")
    if len(rows) != 385 or result.get("state_count") != 385:
        errors.append("state_count")
    if result.get("rows_sha256") != canonical_sha(rows):
        errors.append("rows_sha256")

    expected_state_keys = set()
    counts = {
        name: {"selected": {"CURRENT": 0, "TEMPORAL": 0, "VERIFY": 0, "FULL": 0, "DEFER": 0},
               "deadline_violation": 0, "evidence_violation": 0, "unsafe": 0, "false_defer": 0}
        for name in POLICIES
    }
    temporal_witness = None
    verify_witness = None

    for slack in range(0, 11):
        for reserve in range(0, 5):
            for req in required_sets():
                expected_state_keys.add((slack, reserve, tuple(sorted(req))))

    seen = set()
    for row in rows:
        key = (int(row["slack"]), int(row["reserve"]), tuple(sorted(row["required"])))
        if key in seen:
            errors.append("duplicate_state")
        seen.add(key)
        slack, reserve = key[0], key[1]
        req = frozenset(key[2])
        expected_feasible = feasible(slack, reserve, req)
        if bool(row.get("feasible")) != expected_feasible:
            errors.append(f"feasible:{row.get('index')}")

        for policy in POLICIES:
            expected_choice = select(policy, slack, reserve, req)
            got = row.get("decisions", {}).get(policy)
            if got != expected_choice:
                errors.append(f"decision:{policy}:{row.get('index')}")
                continue
            expected_metrics = classify(slack, reserve, req, got)
            if row.get("metrics", {}).get(policy) != expected_metrics:
                errors.append(f"metrics:{policy}:{row.get('index')}")
            counts[policy]["selected"][got] += 1
            for k in ["deadline_violation", "evidence_violation", "unsafe", "false_defer"]:
                counts[policy][k] += int(expected_metrics[k])

        if classify(slack, reserve, req, select("CURRENT_ONLY", slack, reserve, req))["false_defer"]:
            if ROLE_TEMPORAL in req and temporal_witness is None:
                temporal_witness = row
            if ROLE_VERIFY in req and verify_witness is None:
                verify_witness = row

    if seen != expected_state_keys:
        errors.append("state_set")
    if result.get("policy_counts") != counts:
        errors.append("summary:policy_counts")

    t = {ROLE_CURRENT, ROLE_TEMPORAL}
    v = {ROLE_CURRENT, ROLE_VERIFY}
    incomparable = not t.issubset(v) and not v.issubset(t)
    if result.get("temporal_verify_equal_cost_incomparable") is not True or not incomparable:
        errors.append("incomparability")
    if result.get("temporal_only_evidence_witness") != [ROLE_TEMPORAL]:
        errors.append("temporal_only_witness")
    if result.get("verify_only_evidence_witness") != [ROLE_VERIFY]:
        errors.append("verify_only_witness")

    pass_expected = (
        counts["TYPED_RESERVED"]["unsafe"] == 0
        and counts["TYPED_RESERVED"]["false_defer"] == 0
        and counts["SCALAR_RAW_HIGHEST"]["deadline_violation"] > 0
        and counts["SCALAR_RAW_HIGHEST"]["evidence_violation"] > 0
        and counts["SCALAR_RESERVED_HIGHEST"]["deadline_violation"] == 0
        and counts["SCALAR_RESERVED_HIGHEST"]["evidence_violation"] > 0
        and counts["SCALAR_RESERVED_POSTCHECK"]["unsafe"] == 0
        and counts["SCALAR_RESERVED_POSTCHECK"]["false_defer"] > 0
        and counts["CURRENT_ONLY"]["unsafe"] == 0
        and temporal_witness is not None
        and verify_witness is not None
        and incomparable
    )
    expected_decision = "PASS_ANYTIME_FIDELITY_TYPED_ADMISSION_SCOPED" if pass_expected else "HOLD_OR_FAIL"
    if result.get("decision") != expected_decision:
        errors.append("summary:decision")

    if source_root is not None:
        if not isinstance(freeze, dict):
            errors.append("freeze_missing")
        else:
            sources = freeze.get("sources", {})
            for name in SOURCE_FILES:
                if sources.get(name) != file_sha(source_root / name):
                    errors.append(f"source_hash:{name}")

    return errors


def corruption_controls(rows, result, source_root, freeze):
    outcomes = {}

    r1 = copy.deepcopy(rows)
    r1[0]["decisions"]["TYPED_RESERVED"] = "CURRENT" if r1[0]["decisions"]["TYPED_RESERVED"] != "CURRENT" else "DEFER"
    outcomes["typed_row_mutation_detected"] = bool(audit_objects(r1, result, source_root, freeze))

    s2 = copy.deepcopy(result)
    for entry in s2["catalog"]:
        if entry["name"] == "TEMPORAL":
            entry["evidence"] = ["CURRENT", "TEMPORAL", "VERIFY"]
    outcomes["catalog_mutation_detected"] = bool(audit_objects(rows, s2, source_root, freeze))

    s3 = copy.deepcopy(result)
    s3["policy_counts"]["TYPED_RESERVED"]["unsafe"] += 1
    outcomes["summary_mutation_detected"] = bool(audit_objects(rows, s3, source_root, freeze))
    return outcomes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--source-root", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    source_root = Path(args.source_root)
    rows = json.loads((root / "ROWS.json").read_text(encoding="utf-8"))
    result = json.loads((root / "RESULT.json").read_text(encoding="utf-8"))
    freeze = json.loads((source_root / "FREEZE.json").read_text(encoding="utf-8"))
    errors = audit_objects(rows, result, source_root, freeze)
    corrupt = corruption_controls(rows, result, source_root, freeze)
    out = {"errors": errors, "corruption_controls": corrupt, "pass": (not errors and all(corrupt.values()))}
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if out["pass"] else 3)


if __name__ == "__main__":
    main()
