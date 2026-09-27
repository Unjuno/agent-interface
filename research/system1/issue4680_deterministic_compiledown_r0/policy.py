"""Candidate package compiler/evaluators; intentionally small and deterministic."""
from itertools import product

INTENTS = ("TRACK", "STABILIZE", "WATCH_ONLY", "OUT_OF_SCOPE")
EVIDENCE = ("CLEAR", "MISSING", "AMBIGUOUS", "STALE")
BOOLS = (False, True)
ACTIONS = {"CONTINUE", "CORRECT", "WATCH", "YIELD", "NO_ACTION"}


def valid_package(package):
    return (
        package.get("skill_id") == "bounded-progress-v1"
        and package.get("intent_version") == 1
        and set(package.get("allowed_actions", [])) == ACTIONS
        and "SUBMIT" in package.get("forbidden_effects", [])
    )


def direct(package, row):
    if not valid_package(package):
        return "YIELD"
    if row["intent"] not in INTENTS:
        return "YIELD"
    if row["evidence"] != "CLEAR" or not row["generation_fresh"]:
        return "YIELD"
    if row["forbidden_effect"]:
        return "YIELD"
    if row["completed"]:
        return "NO_ACTION"
    if row["intent"] == "TRACK":
        return "CONTINUE" if row["progressing"] else "CORRECT"
    if row["intent"] == "STABILIZE":
        return "CORRECT" if not row["progressing"] else "CONTINUE"
    if row["intent"] == "WATCH_ONLY":
        return "WATCH"
    return "YIELD"


def key(row):
    return (row["intent"], row["evidence"], row["progressing"], row["completed"],
            row["generation_fresh"], row["forbidden_effect"])


def compile_table(package):
    if not valid_package(package):
        raise ValueError("INVALID_PACKAGE")
    table = {}
    for intent, evidence, progressing, completed, fresh, forbidden in product(
        INTENTS, EVIDENCE, BOOLS, BOOLS, BOOLS, BOOLS
    ):
        row = {"intent": intent, "evidence": evidence, "progressing": progressing,
               "completed": completed, "generation_fresh": fresh,
               "forbidden_effect": forbidden}
        table[key(row)] = direct(package, row)
    return table


def compiled(table, row):
    try:
        return table[key(row)]
    except KeyError:
        return "YIELD"


def make_rows():
    return [
        {"intent": i, "evidence": e, "progressing": p, "completed": c,
         "generation_fresh": f, "forbidden_effect": x}
        for i, e, p, c, f, x in product(INTENTS, EVIDENCE, BOOLS, BOOLS, BOOLS, BOOLS)
    ]


def activate(active_bytes, candidate):
    """Return candidate only when valid; otherwise preserve active bytes exactly."""
    if not valid_package(candidate):
        return active_bytes, False
    return candidate, True
