"""Independent raw-event oracle; deliberately does not import candidate code."""


def reconstruct(rows):
    decisions = []
    for row in rows:
        if row.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        link = row.get("lineage", {})
        lease = link.get("lease_id")
        action = link.get("actuation_id")
        if not lease:
            verdict = "HOLD_MISSING_EDGE_LEASE"
        elif not action:
            verdict = "HOLD_MISSING_EDGE_ACTUATION"
        else:
            authorities = [
                ev.get("lineage", {}).get("actuation_id")
                for ev in rows
                if ev.get("event_type") == "LEASE_OPEN"
                and ev.get("lineage", {}).get("lease_id") == lease
            ]
            if len(authorities) == 0:
                verdict = "HOLD_LEASE_OPEN_MISSING"
            elif len(authorities) > 1:
                verdict = "HOLD_AMBIGUOUS_LEASE_BINDING"
            elif authorities[0] is None:
                verdict = "HOLD_MISSING_LEASE_ACTUATION"
            elif authorities[0] != action:
                verdict = "REJECT_ACTUATION_MISMATCH"
            else:
                verdict = "AUTHORIZED_MATCH"
        decisions.append({"event_id": row.get("event_id"), "status": verdict})
    return decisions or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
