"""Strict independent audit of retained #5216 booleans plus explicit time facts."""
from __future__ import annotations

EXPECTED_KEYS = {
    "execution_end_700", "execution_end_999", "execution_end_1000",
    "execution_end_1001", "execution_wrong_command",
    "effect_at_499", "effect_at_699", "effect_at_700", "effect_at_701",
}
TIMES = {
    "lease_valid_until": 1000,
    "execution_started": 500,
    "execution_ends": {
        "execution_end_700": 700, "execution_end_999": 999,
        "execution_end_1000": 1000, "execution_end_1001": 1001,
    },
    "release_observed": 800,
    "effect_observed": {
        "effect_at_499": 499, "effect_at_699": 699,
        "effect_at_700": 700, "effect_at_701": 701,
    },
    "effect_execution_end": 700,
}
# Each case's expected acceptance is derived independently from declared contract.
def expected_cases():
    out = {}
    for name, end in TIMES["execution_ends"].items():
        out[name] = end < TIMES["lease_valid_until"] and TIMES["release_observed"] >= end
    out["execution_wrong_command"] = False
    for name, observed in TIMES["effect_observed"].items():
        out[name] = observed >= TIMES["execution_started"] and observed >= TIMES["effect_execution_end"]
    return out

def audit(record):
    if type(record) is not dict:
        return {"disposition": "HOLD_SCHEMA", "errors": ["record_not_object"]}
    errors = []
    keys = set(record)
    if keys != EXPECTED_KEYS:
        errors.append("required_key_set_mismatch")
    for key, value in record.items():
        if type(value) is not bool:
            errors.append("non_boolean:" + str(key))
    expected = expected_cases()
    for key, value in expected.items():
        if type(record.get(key)) is not bool:
            continue
        if record[key] is not value:
            errors.append("outcome_mismatches_timestamp_or_identity:" + key)
    # Legacy plan says effect_at_700 must reject, while old auditor treated it as valid.
    # Explicitly surface rather than resolving historical ambiguity silently.
    plan_conflicts = ["effect_at_700"] if expected["effect_at_700"] else []
    disposition = "HOLD_LEGACY_PLAN_CONFLICT" if plan_conflicts and not errors else (
        "PASS_AUDIT_MUTATION_RESISTANCE_SCOPED" if not errors else "HOLD_SCHEMA_OR_CONTRACT"
    )
    return {
        "disposition": disposition,
        "errors": errors,
        "unexpected_keys": sorted(keys - EXPECTED_KEYS),
        "missing_keys": sorted(EXPECTED_KEYS - keys),
        "plan_conflicts": plan_conflicts,
        "expected_cases": expected,
    }
