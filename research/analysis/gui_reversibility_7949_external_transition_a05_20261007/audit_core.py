"""Independent event replay and recovery oracle; no candidate imports."""
from itertools import product


def verify(model, raw):
    errors = []
    if raw.get("run_id") != model.get("run_id"):
        return ["run_id mismatch"]
    rows = {row.get("id"): row for row in raw.get("cases", [])}
    cases = model["cases"]
    if list(rows) != [case["id"] for case in cases]:
        errors.append("case identity/order mismatch")
        return errors
    for case in cases:
        row = rows[case["id"]]
        state = case["events"][0]["before"] if case["events"] else case["start"]
        revision = case["base_revision"]
        integrity = "OK"
        for seq, event in enumerate(case["events"], start=1):
            if event["seq"] != seq or event["revision"] != revision + 1 or event["before"] != state:
                integrity = "UNKNOWN_EVENT_CHAIN"
                break
            if event.get("writer") != "external" or not event.get("event_id"):
                integrity = "UNKNOWN_EVENT_PROVENANCE"
                break
            state, revision = event["after"], event["revision"]
        if integrity != "OK":
            if row.get("label") != integrity or row.get("recovery") is not None:
                errors.append(case["id"] + " invalid history was not fail-closed as " + integrity)
            continue
        if state != case["start"] or revision != case["snapshot_revision"]:
            errors.append(case["id"] + " snapshot does not match replay")
            continue
        if case["certificate_revision"] != case["snapshot_revision"]:
            if row.get("stale", {}).get("label") != "UNKNOWN_STALE_CERTIFICATE" or row.get("stale", {}).get("recovery") is not None:
                errors.append("stale certificate was accepted")
            refreshed = row.get("refreshed", {})
            expected = _oracle(case["recovery"], state, case["target"], model["horizon"])
            if expected is None or refreshed.get("label") != "UNIVERSALLY_UNIFORM" or refreshed.get("final") != case["target"]:
                errors.append("fresh certificate disagrees with independent sequence oracle")
            if case["start"][1:] != case["target"][1:] or refreshed.get("final", "")[1:] != case["start"][1:]:
                errors.append("external fields were not preserved")
        else:
            expected = _oracle(case["recovery"], state, case["target"], model["horizon"])
            if expected is None or row.get("label") != "UNIVERSALLY_UNIFORM" or row.get("final") != case["target"]:
                errors.append(case["id"] + " disagrees with independent sequence oracle")
    return errors


def _oracle(operations, start, target, horizon):
    names = list(operations)
    for size in range(horizon + 1):
        for seq in product(names, repeat=size):
            state = start
            for action in seq:
                state = operations[action].get(state, state)
            if state == target:
                return list(seq)
    return None
