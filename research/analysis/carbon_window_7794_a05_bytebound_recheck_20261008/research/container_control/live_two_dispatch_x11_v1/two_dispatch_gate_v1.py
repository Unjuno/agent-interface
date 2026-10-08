"""One-use post-authority replan gate for model-free two-dispatch integration."""
from __future__ import annotations
from dataclasses import dataclass
from authority_ended_bridge_v1 import to_caller_execution_decision

@dataclass
class ReplanToken:
    post_sequence: int
    used: bool = False


def open_replan_token(receipt):
    decision = to_caller_execution_decision(receipt)
    if decision != {"status":"safe_yield","reason":"authority_unavailable",
                    "completed_actions":receipt["steps_completed"]}:
        raise ValueError("unexpected bridge decision")
    return ReplanToken(post_sequence=receipt["post_authority"]["sequence"])


def current_revalidation(token, current_sequence, *, association_changed=False):
    if token.used:
        return {"status":"token_replay"}
    if type(current_sequence) is not int or current_sequence <= token.post_sequence:
        return {"status":"stale"}
    if association_changed:
        return {"status":"association_changed"}
    return {"status":"revalidated"}


def consume_for_execute(token):
    if token.used:
        raise ValueError("replan token already used")
    token.used=True
