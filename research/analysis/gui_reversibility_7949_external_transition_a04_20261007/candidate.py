"""Candidate for event-bound certificate invalidation, standard library only."""
from itertools import product


def replay(case):
    if case.get("coverage_complete") is not True:
        return None, "UNKNOWN_COVERAGE"
    state = case["events"][0]["before"] if case["events"] else case["start"]
    revision = case["base_revision"]
    expected_seq = 1
    for event in case["events"]:
        if event["seq"] != expected_seq or event["revision"] != revision + 1 or event["before"] != state:
            return None, "UNKNOWN_EVENT_CHAIN"
        state = event["after"]
        revision = event["revision"]
        expected_seq += 1
    if state != case["start"] or revision != case["snapshot_revision"]:
        return None, "UNKNOWN_SNAPSHOT_MISMATCH"
    if case["certificate_revision"] != case["snapshot_revision"]:
        return None, "UNKNOWN_STALE_CERTIFICATE"
    return state, "CURRENT_CERTIFICATE"


def classify(case, start=None):
    state, reason = replay(case)
    if state is None:
        return {"label": reason, "recovery": None}
    start = state if start is None else start
    operations = list(case["recovery"].items())
    names = [name for name, _ in operations]
    for size in range(case.get("horizon", 1) + 1):
        for seq in product(names, repeat=size):
            final = start
            for name in seq:
                final = dict(operations)[name].get(final, final)
            if final == case["target"]:
                return {"label": "UNIVERSALLY_UNIFORM", "recovery": list(seq), "final": final}
    return {"label": "PARTIALLY_RECOVERABLE", "recovery": None}


def run(model):
    result = []
    for case in model["cases"]:
        if case["id"] == "stale_then_refreshed":
            stale = classify(case)
            refreshed = dict(case)
            refreshed["certificate_revision"] = case["snapshot_revision"]
            result.append({"id": case["id"], "stale": stale,
                           "refreshed": classify(refreshed),
                           "external_bit_preserved": case["start"][1] == "1" and case["target"][1] == "1"})
        else:
            result.append({"id": case["id"], **classify(case)})
    return result
