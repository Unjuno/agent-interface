"""Independent raw-row oracle for the W2 lease-close candidate."""


def reconstruct(raw_events):
    lease_open_bindings = {}
    lease_closures = {}
    for row in raw_events:
        link = row.get("lineage", {})
        lease = link.get("lease_id")
        kind = row.get("event_type")
        if kind == "LEASE_OPEN" and lease:
            lease_open_bindings.setdefault(lease, []).append(link.get("actuation_id"))
        if kind == "LEASE_CLOSE" and lease:
            lease_closures.setdefault(lease, []).append(row)

    answer = []
    for sample in raw_events:
        if sample.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        link = sample.get("lineage", {})
        lease, action = link.get("lease_id"), link.get("actuation_id")
        verdict = None
        if not lease:
            verdict = "HOLD_MISSING_EDGE_LEASE"
        elif not action:
            verdict = "HOLD_MISSING_EDGE_ACTUATION"
        elif lease not in lease_open_bindings:
            verdict = "HOLD_LEASE_OPEN_MISSING"
        elif len(lease_open_bindings[lease]) != 1:
            verdict = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif lease_open_bindings[lease][0] is None:
            verdict = "HOLD_MISSING_LEASE_ACTUATION"
        elif lease_open_bindings[lease][0] != action:
            verdict = "REJECT_ACTUATION_MISMATCH"
        else:
            physical = sample.get("payload", {}).get("transition_interval_ns")
            if (not isinstance(physical, list) or len(physical) != 2
                    or not all(type(x) is int for x in physical)
                    or physical[0] < 0 or physical[1] < physical[0]):
                verdict = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                verdict = "AUTHORIZED_MATCH"
                start, finish = physical
                for stop in lease_closures.get(lease, []):
                    stop_link = stop.get("lineage", {})
                    if stop_link.get("actuation_id") != action:
                        verdict = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                        break
                    clock = stop.get("time", {})
                    left, right = clock.get("lower_ns"), clock.get("upper_ns")
                    if (type(left) is not int or type(right) is not int
                            or left < 0 or right < left):
                        verdict = "HOLD_UNKNOWN_CLOSE_TIME"
                        break
                    if right < start:
                        verdict = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                        break
                    if finish >= left:
                        verdict = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                        break
        answer.append({"event_id": sample.get("event_id"), "status": verdict})
    return answer or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
