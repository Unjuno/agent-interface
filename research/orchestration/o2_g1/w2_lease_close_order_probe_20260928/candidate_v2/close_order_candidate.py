"""Conservative candidate for W2 lease-close ordering; construction only."""


def _time_interval(event):
    time = event.get("time") or {}
    lo, hi = time.get("lower_ns"), time.get("upper_ns")
    if not isinstance(lo, int) or isinstance(lo, bool):
        return None
    if not isinstance(hi, int) or isinstance(hi, bool) or hi < lo:
        return None
    return lo, hi


def _edge_interval(event):
    bounds = (event.get("payload") or {}).get("transition_interval_ns")
    if not isinstance(bounds, list) or len(bounds) != 2:
        return None
    lo, hi = bounds
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in bounds) or lo < 0 or hi < lo:
        return None
    return lo, hi


def evaluate(events):
    opens_by_lease = {}
    closes_by_lease = {}
    for event in events:
        lineage = event.get("lineage") or {}
        lease_id = lineage.get("lease_id")
        if event.get("event_type") == "LEASE_OPEN" and lease_id:
            opens_by_lease.setdefault(lease_id, []).append(lineage.get("actuation_id"))
        elif event.get("event_type") == "LEASE_CLOSE" and lease_id:
            closes_by_lease.setdefault(lease_id, []).append(event)

    decisions = []
    terminal_times = []
    for event in events:
        if event.get("event_type") in {"PROGRAM_TERMINAL", "TERMINAL_RESULT"}:
            interval = _time_interval(event)
            if interval is None:
                terminal_times.append(None)
            else:
                terminal_times.append(interval)
    for edge in (e for e in events if e.get("event_type") == "INPUT_EDGE_BRACKET"):
        lineage = edge.get("lineage") or {}
        lease_id, actuation_id = lineage.get("lease_id"), lineage.get("actuation_id")
        if not lease_id:
            status = "HOLD_MISSING_EDGE_LEASE"
        elif not actuation_id:
            status = "HOLD_MISSING_EDGE_ACTUATION"
        elif lease_id not in opens_by_lease:
            status = "HOLD_LEASE_OPEN_MISSING"
        elif len(opens_by_lease[lease_id]) != 1:
            status = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif not opens_by_lease[lease_id][0]:
            status = "HOLD_MISSING_LEASE_ACTUATION"
        elif opens_by_lease[lease_id][0] != actuation_id:
            status = "REJECT_ACTUATION_MISMATCH"
        else:
            edge_interval = _edge_interval(edge)
            if edge_interval is None:
                status = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                status = "AUTHORIZED_MATCH"
                for close in closes_by_lease.get(lease_id, []):
                    close_lineage = close.get("lineage") or {}
                    if close_lineage.get("actuation_id") != actuation_id:
                        status = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                        break
                    close_interval = _time_interval(close)
                    if close_interval is None:
                        status = "HOLD_UNKNOWN_CLOSE_TIME"
                        break
                    edge_lo, edge_hi = edge_interval
                    close_lo, close_hi = close_interval
                    if close_hi < edge_lo:
                        status = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                        break
                    if not edge_hi < close_lo:
                        status = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                        break
                if status == "AUTHORIZED_MATCH" and terminal_times:
                    for interval in terminal_times:
                        if interval is None:
                            status = "HOLD_UNKNOWN_TERMINAL_TIME"
                            break
                        terminal_lo, terminal_hi = interval
                        if edge_interval[1] < terminal_lo:
                            continue
                        if terminal_hi < edge_interval[0]:
                            status = "REJECT_EDGE_AFTER_TERMINAL"
                            break
                        status = "HOLD_EDGE_TERMINAL_ORDER_UNCERTAIN"
                        break
        decisions.append({"event_id": edge.get("event_id"), "status": status})
    return decisions or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
