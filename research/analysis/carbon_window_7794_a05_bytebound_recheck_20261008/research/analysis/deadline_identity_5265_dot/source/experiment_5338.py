"""Authority-neutral candidate for the finite Issue #5265 state-machine probe."""
import hashlib
import json


POLICIES = ("NO_CROSS_PRODUCER_COALESCING", "SEMANTIC_EFFECT_COALESCING")
IDENTITY_FIELDS = (
    "intent_revision",
    "state_generation",
    "target_id",
    "target_incarnation",
    "operation",
    "effect_class",
    "effect_opportunity",
    "expected_postcondition",
    "parameters",
    "deadline_ms",
)


def _effect_identity(proposal):
    values = [proposal.get(field) for field in IDENTITY_FIELDS]
    if any(value is None or value == "" for value in values) or \
            not isinstance(proposal.get("proposal_id"), str) or not proposal["proposal_id"] or \
            not isinstance(proposal.get("producer_id"), str) or not proposal["producer_id"]:
        return None
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def execute_proposals(proposals, policy):
    if policy not in POLICIES:
        raise ValueError("unknown_policy")
    decisions = []
    executed = {}
    groups = []
    for proposal in proposals:
        if proposal.get("retry_of") is not None:
            decisions.append("DEFER_TO_ISSUE_24")
            continue
        now, deadline = proposal.get("now_ms"), proposal.get("deadline_ms")
        if type(now) is not int or type(deadline) is not int:
            decisions.append("YIELD")
            continue
        if now >= deadline:
            decisions.append("YIELD_EXPIRED")
            continue
        if proposal.get("already_satisfied") is True:
            decisions.append("NO_ACTION")
            continue
        identity = _effect_identity(proposal)
        if identity is None:
            decisions.append("YIELD")
            continue
        if policy == "SEMANTIC_EFFECT_COALESCING" and identity in executed:
            groups[executed[identity]]["members"].append({
                "proposal_id": proposal["proposal_id"],
                "producer_id": proposal["producer_id"],
            })
            decisions.append("COALESCED")
            continue
        group_index = len(groups)
        if policy == "SEMANTIC_EFFECT_COALESCING":
            executed[identity] = group_index
        groups.append({
            "members": [{"proposal_id": proposal["proposal_id"],
                         "producer_id": proposal["producer_id"]}],
            "deadline_ms": deadline,
        })
        decisions.append("EXECUTE")
    return {"policy": policy, "decisions": decisions,
            "effects": decisions.count("EXECUTE"), "coalesced_groups": groups}
