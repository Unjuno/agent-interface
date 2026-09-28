"""Contract-aligned W2 authority candidate: LEASE_CLOSE, not program terminal, bounds authority."""


def interval(row):
    time = row.get("time") or {}
    lo, hi = time.get("lower_ns"), time.get("upper_ns")
    if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo:
        return None
    return lo, hi


def edge_interval(row):
    bounds = (row.get("payload") or {}).get("transition_interval_ns")
    if not isinstance(bounds, list) or len(bounds) != 2:
        return None
    lo, hi = bounds
    if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo:
        return None
    return lo, hi


def decide(events):
    opens, closes = {}, {}
    for row in events:
        link = row.get("lineage") or {}
        lease = link.get("lease_id")
        if row.get("event_type") == "LEASE_OPEN" and lease:
            opens.setdefault(lease, []).append(link.get("actuation_id"))
        elif row.get("event_type") == "LEASE_CLOSE" and lease:
            closes.setdefault(lease, []).append(row)

    result = []
    for row in events:
        if row.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        link = row.get("lineage") or {}
        lease, actuation = link.get("lease_id"), link.get("actuation_id")
        if not lease:
            status = "HOLD_MISSING_EDGE_LEASE"
        elif not actuation:
            status = "HOLD_MISSING_EDGE_ACTUATION"
        elif lease not in opens:
            status = "HOLD_LEASE_OPEN_MISSING"
        elif len(opens[lease]) != 1:
            status = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif not opens[lease][0]:
            status = "HOLD_MISSING_LEASE_ACTUATION"
        elif opens[lease][0] != actuation:
            status = "REJECT_ACTUATION_MISMATCH"
        else:
            edge = edge_interval(row)
            if edge is None:
                status = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                status = "AUTHORIZED_MATCH"
                for close in closes.get(lease, []):
                    if (close.get("lineage") or {}).get("actuation_id") != actuation:
                        status = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                        break
                    closed = interval(close)
                    if closed is None:
                        status = "HOLD_UNKNOWN_CLOSE_TIME"
                        break
                    # The edge is definitely after closure only when the entire
                    # edge interval begins strictly after the close interval.
                    if closed[1] < edge[0]:
                        status = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                        break
                    if edge[1] >= closed[0]:
                        status = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                        break
        result.append({"event_id": row.get("event_id"), "status": status})
    return result or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
