"""Versioned task-scoped lifecycle wrapper around the frozen R02 schema."""
from __future__ import annotations


TRANSIENT_GUARD_PREDICATES = frozenset({"target_valid"})


def compile_contract_v2(contract, aliases, scope, *, compile_contract):
    """Keep transient target checks in branches/admission, never post-effects."""
    for action in contract.get("actions", []):
        predicates = {item.get("predicate") for item in action.get("expected_effect", [])
                      if type(item) is dict}
        invalid = predicates & TRANSIENT_GUARD_PREDICATES
        if invalid:
            raise ValueError(
                "transient guard predicate cannot be an action expected_effect: "
                + ",".join(sorted(invalid))
            )
    return compile_contract(contract, aliases, scope)
