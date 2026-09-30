"""Independent raw-row authority reconstruction including open and close intervals."""


def _clock_bounds(event):
    clock = event.get("time", {})
    left, right = clock.get("lower_ns"), clock.get("upper_ns")
    if type(left) is not int or type(right) is not int or left < 0 or right < left:
        return None
    return left, right


def _physical_bounds(event):
    bounds = event.get("payload", {}).get("transition_interval_ns")
    if (not isinstance(bounds, list) or len(bounds) != 2
            or type(bounds[0]) is not int or type(bounds[1]) is not int
            or bounds[0] < 0 or bounds[1] < bounds[0]):
        return None
    return bounds[0], bounds[1]


def audit(raw_rows):
    by_open, by_stop = {}, {}
    for item in raw_rows:
        refs = item.get("lineage", {})
        owner = refs.get("lease_id")
        if item.get("event_type") == "LEASE_OPEN" and owner:
            by_open.setdefault(owner, []).append(item)
        if item.get("event_type") == "LEASE_CLOSE" and owner:
            by_stop.setdefault(owner, []).append(item)

    output = []
    for item in raw_rows:
        if item.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        refs = item.get("lineage", {})
        owner, action = refs.get("lease_id"), refs.get("actuation_id")
        decision = "AUTHORIZED_MATCH"
        if not owner:
            decision = "HOLD_MISSING_EDGE_LEASE"
        elif not action:
            decision = "HOLD_MISSING_EDGE_ACTUATION"
        elif owner not in by_open:
            decision = "HOLD_LEASE_OPEN_MISSING"
        elif len(by_open[owner]) != 1:
            decision = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif by_open[owner][0].get("lineage", {}).get("actuation_id") is None:
            decision = "HOLD_MISSING_LEASE_ACTUATION"
        elif by_open[owner][0].get("lineage", {}).get("actuation_id") != action:
            decision = "REJECT_ACTUATION_MISMATCH"
        else:
            physical = _physical_bounds(item)
            if physical is None:
                decision = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                opened = _clock_bounds(by_open[owner][0])
                if opened is None:
                    decision = "HOLD_UNKNOWN_LEASE_OPEN_TIME"
                elif physical[1] < opened[0]:
                    decision = "REJECT_EDGE_BEFORE_LEASE_OPEN"
                elif opened[1] >= physical[0]:
                    decision = "HOLD_EDGE_LEASE_OPEN_ORDER_UNCERTAIN"
                else:
                    for stopped in by_stop.get(owner, []):
                        stop_refs = stopped.get("lineage", {})
                        if stop_refs.get("actuation_id") != action:
                            decision = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                            break
                        stopped_at = _clock_bounds(stopped)
                        if stopped_at is None:
                            decision = "HOLD_UNKNOWN_CLOSE_TIME"
                            break
                        if stopped_at[1] < physical[0]:
                            decision = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                            break
                        if physical[1] >= stopped_at[0]:
                            decision = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                            break
        output.append({"event_id": item.get("event_id"), "status": decision})
    return output or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
