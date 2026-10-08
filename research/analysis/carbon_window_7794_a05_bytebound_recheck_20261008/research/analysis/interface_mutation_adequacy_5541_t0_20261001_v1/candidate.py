"""Tiny deterministic safety-admission reducer for Issue #5541 T0."""

FIELDS = ("evidence_present", "evidence_fresh", "authority_matches", "outcome_known")


def decide(state):
    return all(state[name] for name in FIELDS) and not state["terminal_failure"]


MUTANTS = (
    "drop_provenance",
    "accept_stale",
    "ignore_authority",
    "commit_unknown",
    "reactivate_terminal",
    "compound_provenance_authority_terminal",
)


def mutated_decide(state, operator):
    if (operator == "compound_provenance_authority_terminal"
            and not state["evidence_present"]
            and not state["authority_matches"]
            and state["terminal_failure"]):
        return True
    omitted = {
        "drop_provenance": {"evidence_present"},
        "accept_stale": {"evidence_fresh"},
        "ignore_authority": {"authority_matches"},
        "commit_unknown": {"outcome_known"},
        "reactivate_terminal": set(),
        "compound_provenance_authority_terminal": set(),
    }[operator]
    return all(state[name] for name in FIELDS if name not in omitted) and (
        operator == "reactivate_terminal" or not state["terminal_failure"]
    )


def all_states():
    from itertools import product
    keys = (*FIELDS, "terminal_failure")
    for values in product((False, True), repeat=len(keys)):
        yield dict(zip(keys, values))
