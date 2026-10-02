"""Independent lease-authority reconstruction from raw event rows."""


def reconstruct(rows):
    binding_rows = {}
    closure_rows = {}
    for raw in rows:
        refs = raw.get("lineage", {})
        lid = refs.get("lease_id")
        if raw.get("event_type") == "LEASE_OPEN" and lid:
            binding_rows.setdefault(lid, []).append(refs.get("actuation_id"))
        if raw.get("event_type") == "LEASE_CLOSE" and lid:
            closure_rows.setdefault(lid, []).append(raw)

    audited = []
    for raw in rows:
        if raw.get("event_type") != "INPUT_EDGE_BRACKET":
            continue
        refs = raw.get("lineage", {})
        lid, aid = refs.get("lease_id"), refs.get("actuation_id")
        verdict = None
        if not lid:
            verdict = "HOLD_MISSING_EDGE_LEASE"
        elif not aid:
            verdict = "HOLD_MISSING_EDGE_ACTUATION"
        elif not binding_rows.get(lid):
            verdict = "HOLD_LEASE_OPEN_MISSING"
        elif len(binding_rows[lid]) != 1:
            verdict = "HOLD_AMBIGUOUS_LEASE_BINDING"
        elif binding_rows[lid][0] is None:
            verdict = "HOLD_MISSING_LEASE_ACTUATION"
        elif binding_rows[lid][0] != aid:
            verdict = "REJECT_ACTUATION_MISMATCH"
        else:
            bounds = raw.get("payload", {}).get("transition_interval_ns")
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or type(bounds[0]) is not int or type(bounds[1]) is not int
                    or bounds[0] < 0 or bounds[1] < bounds[0]):
                verdict = "HOLD_UNKNOWN_EDGE_INTERVAL"
            else:
                verdict = "AUTHORIZED_MATCH"
                for stopped in closure_rows.get(lid, []):
                    stop_refs = stopped.get("lineage", {})
                    if stop_refs.get("actuation_id") != aid:
                        verdict = "HOLD_CLOSE_LINEAGE_UNRESOLVED"
                        break
                    stamp = stopped.get("time", {})
                    lo, hi = stamp.get("lower_ns"), stamp.get("upper_ns")
                    if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo:
                        verdict = "HOLD_UNKNOWN_CLOSE_TIME"
                        break
                    if hi < bounds[0]:
                        verdict = "REJECT_EDGE_AFTER_LEASE_CLOSE"
                        break
                    if bounds[1] >= lo:
                        verdict = "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
                        break
        audited.append({"event_id": raw.get("event_id"), "status": verdict})
    return audited or [{"event_id": None, "status": "NO_INPUT_EDGE"}]
