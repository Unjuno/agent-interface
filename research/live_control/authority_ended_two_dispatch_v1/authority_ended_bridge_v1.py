"""Model-free bridge from dual-lifetime executor terminal receipts to caller-v3 execution decisions.

The bridge grants no semantic/input authority. It only converts a fully evidenced
scheduled authority end into caller-v3's existing safe-yield vocabulary. Missing
or malformed post-authority evidence fails closed.
"""
from __future__ import annotations
import copy

class AuthorityEndedNotReady(ValueError):
    pass


def to_caller_execution_decision(receipt):
    if type(receipt) is not dict:
        raise AuthorityEndedNotReady("terminal receipt object required")
    if receipt.get("terminal_status") != "authority_ended":
        raise AuthorityEndedNotReady("scheduled authority_ended status required")
    if receipt.get("release_verified") is not True:
        raise AuthorityEndedNotReady("verified release required")
    if receipt.get("keys_down") != [] or receipt.get("buttons_down") != []:
        raise AuthorityEndedNotReady("verified empty input state required")
    if receipt.get("post_release_input_admissions") != 0:
        raise AuthorityEndedNotReady("post-release input admission forbidden")
    completed = receipt.get("steps_completed")
    if type(completed) is not int or completed < 0:
        raise AuthorityEndedNotReady("nonnegative completed step count required")
    post = receipt.get("post_authority")
    if type(post) is not dict:
        raise AuthorityEndedNotReady("post-authority observation required")
    if post.get("grants_input_authority") is not False:
        raise AuthorityEndedNotReady("post-authority observation must not grant input authority")
    if post.get("tail_program_steps_resumed") != 0:
        raise AuthorityEndedNotReady("old program tail must not resume")
    if post.get("captures") != 1:
        raise AuthorityEndedNotReady("exactly one passive post-authority capture required")
    if type(post.get("sequence")) is not int or post["sequence"] < 1:
        raise AuthorityEndedNotReady("fresh post-authority sequence required")
    if post.get("sequence_advanced") is not True:
        raise AuthorityEndedNotReady("post-authority observation must advance sequence")
    if post.get("error") is not None:
        raise AuthorityEndedNotReady("post-authority observation error")
    if post.get("within_lifecycle_deadline") is not True:
        raise AuthorityEndedNotReady("post-authority observation outside lifecycle deadline")
    finished = post.get("snapshot_finished_ns")
    deadline = post.get("lifecycle_deadline_ns")
    if type(finished) is not int or type(deadline) is not int or finished > deadline:
        raise AuthorityEndedNotReady("post-authority timing receipt invalid")
    # Independent scorer fields, if accidentally present in the source record, are
    # intentionally ignored: they are not caller-visible authority.
    return {"status":"safe_yield", "reason":"authority_unavailable",
            "completed_actions":completed}
