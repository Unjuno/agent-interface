"""W2 lease interval candidate with open and close time bounds; terminal stays separate."""


def _interval(row):
    stamp = row.get("time") or {}
    lo, hi = stamp.get("lower_ns"), stamp.get("upper_ns")
    if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo:
        return None
    return lo, hi


def _edge(row):
    physical = (row.get("payload") or {}).get("transition_interval_ns")
    if not isinstance(physical, list) or len(physical) != 2:
        return None
    lo, hi = physical
    if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo:
        return None
    return lo, hi


def evaluate(events):
    opens, closes = {}, {}
    for row in events:
        refs = row.get("lineage") or {}
        lease = refs.get("lease_id")
        if row.get("event_type") == "LEASE_OPEN" and lease:
            opens.setdefault(lease, []).append(row)
        elif row.get("event_type") == "LEASE_CLOSE" and lease:
            closes.setdefault(lease, []).append(row)

    decisions = []
    for edge_row in events:
        if edge_row.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        refs = edge_row.get("lineage") or {}
        lease, actuation = refs.get("lease_id"), refs.get("actuation_id")
        if not lease:
            status = "HOLD_MISSING_EDGE_LEASE"
        elif not actuation:
            status = "HOLD_MISSING_EDGE_ACTUATION"
        elif lease not in opens:
            status = "HOLD_LEASE_OPEN_MISSING"
        elif len(opens[lease]) != 1:
            status = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif not (opens[lease][0].get("lineage") or {}).get("actuation_id"):
            status = "HOLD_MISSING_LEASE_ACTUATION"
        elif (opens[lease][0].get("lineage") or {}).get("actuation_id") != actuation:
            status = "REJECT_ACTUATION_MISMATCH"
        else:
            physical = _edge(edge_row)
            if physical is None:
                status = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                opened = _interval(opens[lease][0])
                if opened is None:
                    status = "HOLD_UNKNOWN_LEASE_OPEN_TIME"
                elif physical[1] < opened[0]:
                    status = "REJECT_EDGE_BEFORE_LEASE_OPEN"
                elif opened[1] >= physical[0]:
                    status = "HOLD_EDGE_LEASE_OPEN_ORDER_UNCERTAIN"
                else:
                    status = "AUTHORIZED_MATCH"
                    for close_row in closes.get(lease, []):
                        close_refs = close_row.get("lineage") or {}
                        if close_refs.get("actuation_id") != actuation:
                            status = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                            break
                        closed = _interval(close_row)
                        if closed is None:
                            status = "HOLD_UNKNOWN_CLOSE_TIME"
                            break
                        if closed[1] < physical[0]:
                            status = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                            break
                        if physical[1] >= closed[0]:
                            status = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                            break
        decisions.append({"event_id": edge_row.get("event_id"), "status": status})
    return decisions or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
