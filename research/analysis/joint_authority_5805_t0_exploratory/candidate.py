def evaluate_trace(trace, modes):
    return [_decision(trace, mode) for mode in modes]


def _matches(record, trace, principal, epoch):
    return (
        record.get("principal") == principal
        and record.get("resource") == trace["resource"]
        and record.get("effect") == trace["effect"]
        and record.get("recipient") == trace["recipient"]
        and record.get("epoch") == epoch
        and record.get("authentic") is True
    )


def _grant_for_owner(trace, owner):
    epoch = trace["owner_epochs"].get(owner)
    relevant = [g for g in trace["grants"] if
                g.get("principal") == owner
                and g.get("resource") == trace["resource"]
                and g.get("effect") == trace["effect"]
                and g.get("recipient") == trace["recipient"]]
    if any(g.get("authentic") is True and g.get("state") == "DENY"
           and g.get("epoch") == epoch for g in relevant):
        return False
    return any(_matches(g, trace, owner, epoch) and g.get("state") == "ALLOW"
               for g in relevant)


def _delegated_for_owner(trace, owner):
    epoch = trace["owner_epochs"].get(owner)
    return any(
        d.get("principal") == owner
        and d.get("delegate") == trace["requester"]
        and d.get("resource") == trace["resource"]
        and d.get("effect") == trace["effect"]
        and d.get("recipient") == trace["recipient"]
        and d.get("epoch") == epoch
        and d.get("authentic") is True
        for d in trace["delegations"]
    )


def _decision(trace, mode):
    safety_action = trace["safety_action"] and trace["effect"] in ("RELEASE", "CANCEL")
    if safety_action:
        allowed, reason = True, "INDEPENDENT_SAFETY_LANE"
    elif trace["owner_set_status"] != "KNOWN" or not trace["owners"]:
        allowed, reason = False, "HOLD_UNKNOWN_AFFECTED_OWNERS"
    elif mode == "deny_all":
        allowed, reason = False, "DENY_ALL_CONTENT_EFFECTS"
    elif mode == "requester_only":
        if trace["requester"] not in trace["owners"]:
            allowed, reason = False, "REQUESTER_NOT_DECLARED_OWNER"
        else:
            allowed = _grant_for_owner(trace, trace["requester"])
            reason = "REQUESTER_GRANT" if allowed else "MISSING_CURRENT_REQUESTER_GRANT"
    elif mode in ("all_owner_conjunction", "scoped_delegation"):
        allowed = True
        for owner in trace["owners"]:
            if _grant_for_owner(trace, owner):
                continue
            if mode == "scoped_delegation" and owner != trace["requester"] and _delegated_for_owner(trace, owner):
                continue
            allowed = False
            break
        reason = "ALL_REQUIRED_AUTHORITY_PRESENT" if allowed else "MISSING_CONFLICTING_OR_STALE_AUTHORITY"
    else:
        raise ValueError("unknown policy mode")
    return {
        "trace_id": trace["trace_id"],
        "mode": mode,
        "admitted": allowed,
        "attempted": allowed,
        "effect_applied": False,
        "effect_verified": False,
        "reason": reason,
    }
