"""Independent expected-outcome oracle for the Issue #5317 raw matrix."""

import json
import sys


# Each outcome tuple is (admitted, unsafe_prefix, goal_reached, stranded).
EXPECTED = {
    "two_step_unsafe": {
        "POSTHOC_VERIFY": (True, True, False, True),
        "ONE_STEP_FILTER": (True, True, False, True),
        "HORIZON_FILTER": (False, False, False, False),
        "VIABILITY_FILTER": (False, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (False, False, False, False),
    },
    "dead_end": {
        "POSTHOC_VERIFY": (True, False, False, True),
        "ONE_STEP_FILTER": (True, False, False, True),
        "HORIZON_FILTER": (True, False, False, True),
        "VIABILITY_FILTER": (False, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (True, False, False, True),
    },
    "safe_goal": {p: (True, False, True, False) for p in
                  ("POSTHOC_VERIFY", "ONE_STEP_FILTER", "HORIZON_FILTER", "VIABILITY_FILTER", "UNKNOWN_FAIL_CLOSED")},
    "bounded_safe": {
        "POSTHOC_VERIFY": (True, False, False, False),
        "ONE_STEP_FILTER": (True, False, False, False),
        "HORIZON_FILTER": (True, False, False, False),
        "VIABILITY_FILTER": (True, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (False, False, False, False),
    },
    "bounded_with_bad_outcome": {
        "POSTHOC_VERIFY": (True, True, False, True),
        "ONE_STEP_FILTER": (False, False, False, False),
        "HORIZON_FILTER": (False, False, False, False),
        "VIABILITY_FILTER": (False, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (False, False, False, False),
    },
    "missing_transition": {
        "POSTHOC_VERIFY": (True, False, True, False),
        "ONE_STEP_FILTER": (False, False, False, False),
        "HORIZON_FILTER": (False, False, False, False),
        "VIABILITY_FILTER": (False, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (False, False, False, False),
    },
    "stale_optimistic": {
        "POSTHOC_VERIFY": (True, True, False, True),
        "ONE_STEP_FILTER": (False, False, False, False),
        "HORIZON_FILTER": (False, False, False, False),
        "VIABILITY_FILTER": (False, False, False, False),
        "UNKNOWN_FAIL_CLOSED": (False, False, False, False),
    },
}


def audit(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    errors = []
    if raw.get("metadata", {}).get("container_invocations") != 0:
        errors.append("container count mismatch")
    if set(raw.get("cases", {})) != set(EXPECTED):
        errors.append("scenario inventory mismatch")
    for name, policies in EXPECTED.items():
        cells = raw.get("cases", {}).get(name, {}).get("policies", {})
        if set(cells) != set(policies):
            errors.append(f"policy inventory mismatch: {name}")
        for policy, expected in policies.items():
            got = cells.get(policy, {})
            actual = tuple(bool(got.get(field)) for field in
                           ("admitted", "unsafe_prefix", "goal_reached", "stranded"))
            if actual != expected:
                errors.append(f"outcome mismatch: {name}/{policy}: {actual} != {expected}")
            if got.get("authority_created") is not False or got.get("effect_claim_created") is not False:
                errors.append(f"authority/effect leakage: {name}/{policy}")
    return errors


if __name__ == "__main__":
    errors = audit(sys.argv[1])
    print(json.dumps({"status": "PASS_READONLY" if not errors else "FAIL_AUDIT",
                      "scenarios": len(EXPECTED), "policy_cells": sum(map(len, EXPECTED.values())),
                      "errors": errors}, sort_keys=True))
    raise SystemExit(bool(errors))
