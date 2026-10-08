"""Finite revision-bound recovery candidate; standard library only."""
from itertools import product


def replay(case):
    if case.get("coverage_complete") is not True:
        return None, "UNKNOWN_COVERAGE"
    state = case["events"][0]["before"] if case["events"] else case["start"]
    revision = case["base_revision"]
    for seq, event in enumerate(case["events"], start=1):
        if event["seq"] != seq or event["revision"] != revision + 1 or event["before"] != state:
            return None, "UNKNOWN_EVENT_CHAIN"
        if event.get("writer") != "external" or not event.get("event_id"):
            return None, "UNKNOWN_EVENT_PROVENANCE"
        state, revision = event["after"], event["revision"]
    if state != case["start"] or revision != case["snapshot_revision"]:
        return None, "UNKNOWN_SNAPSHOT_MISMATCH"
    if case["certificate_revision"] != case["snapshot_revision"]:
        return None, "UNKNOWN_STALE_CERTIFICATE"
    return state, "CURRENT_CERTIFICATE"


def classify(case):
    state, reason = replay(case)
    if state is None:
        return {"label": reason, "recovery": None, "final": None}
    names = list(case["recovery"])
    for size in range(2):
        for seq in product(names, repeat=size):
            final = state
            for action in seq:
                final = case["recovery"][action].get(final, final)
            if final == case["target"]:
                return {"label": "UNIVERSALLY_UNIFORM", "recovery": list(seq), "final": final}
    return {"label": "PARTIALLY_RECOVERABLE", "recovery": None, "final": state}


def run(model):
    out = []
    for case in model["cases"]:
        if case["id"] == "stale_then_refreshed":
            stale = classify(case)
            fresh = dict(case, certificate_revision=case["snapshot_revision"])
            out.append({"id": case["id"], "stale": stale, "refreshed": classify(fresh)})
        else:
            out.append({"id": case["id"], **classify(case)})
    return out
