"""Candidate rule for exact W2 lease-to-actuation binding (construction only)."""


def evaluate(events):
    opens = {}
    for event in events:
        if event.get("event_type") != "LEASE_OPEN":
            continue
        lineage = event.get("lineage") or {}
        lease_id = lineage.get("lease_id")
        if lease_id is not None:
            opens.setdefault(lease_id, []).append(lineage.get("actuation_id"))

    results = []
    for event in events:
        if event.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        edge = event.get("lineage") or {}
        lease_id = edge.get("lease_id")
        actuation_id = edge.get("actuation_id")
        if not lease_id:
            status = "HOLD_MISSING_EDGE_LEASE"
        elif not actuation_id:
            status = "HOLD_MISSING_EDGE_ACTUATION"
        elif lease_id not in opens:
            status = "HOLD_LEASE_OPEN_MISSING"
        elif len(opens[lease_id]) != 1:
            status = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif opens[lease_id][0] is None:
            status = "HOLD_MISSING_LEASE_ACTUATION"
        elif opens[lease_id][0] != actuation_id:
            status = "REJECT_ACTUATION_MISMATCH"
        else:
            status = "AUTHORIZED_MATCH"
        results.append({"event_id": event.get("event_id"), "status": status})

    return results or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
