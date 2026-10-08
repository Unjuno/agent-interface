#!/usr/bin/env python3
"""Independent raw-data audit; does not import candidate.py."""
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ATOM_NAMES = ("redundancy", "unique_x1", "unique_x2", "synergy", "joint_mi")


def entropy(probabilities):
    return -sum(p * math.log2(p) for p in probabilities.values() if p > 0)


def mutual_information(joint):
    left = Counter(); right = Counter(); total = sum(joint.values())
    for (x, y), count in joint.items():
        left[x] += count
        right[y] += count
    return entropy({x: n / total for x, n in left.items()}) + entropy(
        {y: n / total for y, n in right.items()}
    ) - entropy({pair: n / total for pair, n in joint.items()})


def reference_pid(rows):
    joint = Counter()
    for row in rows:
        count = row.get("count")
        if type(count) is not int or count <= 0:
            raise ValueError("nonpositive/noninteger count")
        x1, x2, y = row.get("x1"), row.get("x2"), row.get("y")
        if any(type(v) is not int for v in (x1, x2, y)):
            raise ValueError("noninteger variable")
        joint[(x1, x2, y)] += count
    total = sum(joint.values())
    x1_y = Counter(); x2_y = Counter(); pair_y = Counter(); y_counts = Counter()
    x1_counts = Counter(); x2_counts = Counter()
    for (x1, x2, y), count in joint.items():
        x1_y[(x1, y)] += count; x2_y[(x2, y)] += count
        pair_y[((x1, x2), y)] += count; y_counts[y] += count
        x1_counts[x1] += count; x2_counts[x2] += count
    mi1 = mutual_information(x1_y)
    mi2 = mutual_information(x2_y)
    mi_pair = mutual_information(pair_y)
    redundancy = 0.0
    for y, count_y in y_counts.items():
        per_source = []
        for source_y, source_counts in ((x1_y, x1_counts), (x2_y, x2_counts)):
            info = 0.0
            for (source, target), count in source_y.items():
                if target == y:
                    conditional = count / count_y
                    marginal = source_counts[source] / total
                    info += conditional * math.log2(conditional / marginal)
            per_source.append(info)
        redundancy += (count_y / total) * min(per_source)
    unique1 = mi1 - redundancy
    unique2 = mi2 - redundancy
    synergy = mi_pair - redundancy - unique1 - unique2
    return {"redundancy": redundancy, "unique_x1": unique1, "unique_x2": unique2,
            "synergy": synergy, "joint_mi": mi_pair}


def audit_data(fixture, result):
    if fixture.get("schema") != "issue7712_pid_t0_fixture_v1":
        return False, "fixture_schema"
    if fixture.get("sources") != ["x1", "x2"] or fixture.get("target") != "y":
        return False, "fixture_identity"
    if result.get("schema") != "issue7712_pid_t0_result_v1":
        return False, "result_schema"
    if result.get("sources") != ["x1", "x2"] or result.get("target") != "y":
        return False, "result_identity"
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    if result.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        return False, "fixture_digest"
    if result.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest():
        return False, "candidate_digest"
    expected_cases = fixture.get("cases")
    actual_rows = result.get("rows")
    if type(expected_cases) is not list or type(actual_rows) is not list or len(expected_cases) != len(actual_rows):
        return False, "row_count"
    if not isinstance(fixture.get("tolerance"), (int, float)) or fixture["tolerance"] != 1e-12:
        return False, "tolerance"
    tolerance = fixture["tolerance"]
    for expected_case, actual in zip(expected_cases, actual_rows):
        if actual.get("id") != expected_case.get("id"):
            return False, "case_identity"
        if actual.get("counts") != expected_case.get("counts"):
            return False, "joint_distribution"
        try:
            atoms = reference_pid(actual["counts"])
        except (KeyError, TypeError, ValueError):
            return False, "invalid_distribution"
        declared = expected_case.get("expected", {})
        observed = actual.get("atoms")
        if type(observed) is not dict or set(observed) != set(ATOM_NAMES):
            return False, "atom_schema"
        for name in ATOM_NAMES:
            value = observed.get(name)
            if type(value) not in (int, float) or not math.isfinite(value):
                return False, "nonfinite_atom"
            if abs(value - atoms[name]) > tolerance or abs(atoms[name] - declared.get(name, math.inf)) > tolerance:
                return False, "atom_value"
        if any(atoms[name] < -tolerance for name in ATOM_NAMES[:-1]):
            return False, "negative_atom"
    return True, "PASS_METHOD_SCOPED"


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
    passed, reason = audit_data(fixture, result)
    record = {"schema": "issue7712_pid_t0_audit_v1", "checks": 6,
              "disposition": reason if passed else "FAIL_AUDIT", "passed": passed}
    (ROOT / "audit.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
