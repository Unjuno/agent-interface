"""Strict, independent adjudicator for retained temporal-receipt evidence."""
from __future__ import annotations

from collections.abc import Mapping, Sequence


REQUIRED_KEYS = frozenset({
    "execution_end_700", "execution_end_999", "execution_end_1000",
    "execution_end_1001", "execution_wrong_command", "effect_at_499",
    "effect_at_699", "effect_at_700", "effect_at_701", "effect_at_900",
})


def adjudicate(record: object, observed_keys: Sequence[str],
               boundary_contract: Mapping[str, object]) -> dict[str, object]:
    """Return HOLD until provenance, schema, and contract are all complete.

    This oracle intentionally does not decide whether equality at execution end
    is valid. The retained PLAN contradicts itself on that point, so no
    acceptance result can be soundly derived from these records.
    """
    if type(record) is not dict or type(observed_keys) not in (list, tuple):
        return {"disposition": "HOLD_SCHEMA", "errors": ["record_and_key_inventory_required"]}
    if any(type(key) is not str for key in observed_keys):
        return {"disposition": "HOLD_SCHEMA", "errors": ["key_inventory_must_be_strings"]}
    inventory = set(observed_keys)
    actual = set(record)
    errors: list[str] = []
    if actual != inventory:
        errors.append("record_keys_differ_from_frozen_observation_inventory")
    if inventory != REQUIRED_KEYS:
        errors.append("frozen_observation_inventory_incomplete_or_unexpected")
    missing = sorted(REQUIRED_KEYS - actual)
    extra = sorted(actual - REQUIRED_KEYS)
    mistyped = sorted(key for key in actual & REQUIRED_KEYS
                      if type(record[key]) is not bool)
    if missing:
        errors.append("required_cases_missing")
    if extra:
        errors.append("unpreregistered_cases_present")
    if mistyped:
        errors.append("case_outcomes_must_be_boolean")
    if errors:
        return {"disposition": "HOLD_SCHEMA", "errors": errors,
                "missing": missing, "extra": extra, "mistyped": mistyped}

    relation = (
        boundary_contract.get("effect_at_700_plan_case"),
        boundary_contract.get("effect_at_700_plan_note"),
        boundary_contract.get("effect_at_700_legacy_audit_expected"),
    )
    if relation != ("reject", "causally eligible", True):
        return {"disposition": "HOLD_BOUNDARY_CONFIGURATION",
                "errors": ["frozen_boundary_sources_differ_from_intake"]}
    return {"disposition": "HOLD_CONTRACT_AMBIGUITY",
            "errors": ["effect_at_700_contract_conflicts_across_plan_and_audit"],
            "lease_deadline_semantics": boundary_contract.get("lease_deadline_semantics")}


def mutate_one(record: dict, key: str, mode: str) -> tuple[dict, list[str]]:
    """Create one isolated field-presence/type mutation and its key inventory."""
    result = dict(record)
    keys = list(record)
    if mode == "missing":
        result.pop(key, None)
        if key in keys:
            keys.remove(key)
    elif mode == "null":
        result[key] = None
    elif mode == "string":
        result[key] = "true"
    elif mode == "integer":
        result[key] = 1
    else:
        raise ValueError("unknown mutation mode")
    return result, keys
