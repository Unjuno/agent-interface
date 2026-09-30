"""Small authority-neutral lifecycle monitor for Issue #5320."""

from dataclasses import dataclass


EDGES = {
    ("OFFERED", "acquire"): "LEASED",
    ("LEASED", "prepare"): "PREPARED",
    ("LEASED", "abort"): "ABORTED",
    ("LEASED", "expire"): "EXPIRED",
    ("PREPARED", "begin_commit"): "COMMITTING",
    ("PREPARED", "abort"): "ABORTED",
    ("PREPARED", "expire"): "EXPIRED",
    ("COMMITTING", "effect_confirmed"): "EFFECT_CONFIRMED",
    ("COMMITTING", "effect_unknown"): "UNKNOWN",
    ("COMMITTING", "cancel_uncertain"): "UNKNOWN",
    ("UNKNOWN", "resolve_confirmed"): "EFFECT_CONFIRMED",
    ("UNKNOWN", "resolve_absent"): "ABORTED",
    ("EFFECT_CONFIRMED", "release"): "RELEASED",
    ("ABORTED", "release"): "RELEASED",
    ("EXPIRED", "reconcile_unknown"): "UNKNOWN",
}


@dataclass(frozen=True)
class Decision:
    accepted: bool
    state: str
    reason: str
    authority: bool = False
    effect_claim: bool = False


def transition(state, event):
    """Advance only on an explicitly declared edge; never infer effects."""
    target = EDGES.get((state, event))
    if target is None:
        return Decision(False, state, "ILLEGAL_TRANSITION")
    if event == "effect_confirmed" or event == "resolve_confirmed":
        # Protocol state may record supplied evidence, but does not create it.
        return Decision(True, target, "EVIDENCE_REQUIRED", effect_claim=False)
    return Decision(True, target, "PROTOCOL_ONLY")


def run(events, policy):
    state = "OFFERED"
    cap = 0
    accepted = []
    illegal = []
    for role, event, cap_id in events:
        syntactically_known = event in {edge[1] for edge in EDGES}
        if policy == "CONVENTION_ONLY":
            ok = syntactically_known
            reason = "CONVENTION_ACCEPTED" if ok else "UNKNOWN_EVENT"
            if ok and (state, event) not in EDGES:
                illegal.append(event)
            if ok:
                state = EDGES.get((state, event), state)
        elif policy == "RUNTIME_AUTOMATON":
            d = transition(state, event)
            ok, reason = d.accepted, d.reason
            if ok:
                state = d.state
        elif policy == "LINEAR_PROTOCOL":
            d = transition(state, event)
            ok = d.accepted and cap_id == cap
            reason = d.reason if not d.accepted else ("CAPABILITY_REPLAY" if cap_id != cap else d.reason)
            if ok:
                state, cap = d.state, cap + 1
        elif policy == "MULTIPARTY_PROTOCOL":
            d = transition(state, event)
            expected_role = {
                "acquire": "owner", "prepare": "broker", "begin_commit": "broker",
                "effect_confirmed": "verifier", "effect_unknown": "verifier",
                "cancel_uncertain": "planner", "resolve_confirmed": "verifier",
                "resolve_absent": "verifier", "release": "owner", "expire": "owner",
                "abort": "planner", "reconcile_unknown": "verifier",
            }.get(event)
            ok = d.accepted and role == expected_role
            reason = d.reason if not d.accepted else ("ROLE_MISMATCH" if role != expected_role else d.reason)
            if ok:
                state = d.state
        else:
            raise ValueError(policy)
        accepted.append(ok)
        if ok and event == "effect_confirmed":
            # Monitor records protocol progression only, never external truth.
            pass
    return {"policy": policy, "accepted": accepted, "illegal_attempts": illegal,
            "final_state": state, "authority_created": False,
            "effect_claim_created": False}
