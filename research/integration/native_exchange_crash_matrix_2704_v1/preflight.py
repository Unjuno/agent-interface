"""Disposable-owner crash-loss-point preflight; never grants replay authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


LOSS_POINTS = (
    "before_request_commit", "after_request_commit_before_owner_launch",
    "during_owner_wait", "after_emission_before_reply_commit",
    "after_reply_commit_before_ack", "read_only_resume",
)


def digest(value: dict) -> str:
    return hashlib.sha256((json.dumps(value, sort_keys=True) + "\n").encode()).hexdigest()


def plan_case(root: Path, loss_point: str) -> dict:
    if loss_point not in LOSS_POINTS:
        raise ValueError("unknown registered loss point")
    request = {"request_id": "request-2704-01", "action_id": "action-2704-01",
               "decision": {"source_sequence": 1, "operation": "disposable_effect"}}
    return {"loss_point": loss_point, "request": request,
            "decision_sha256": digest(request["decision"]),
            "native_fixture": False, "authority_granted": False,
            "replay_allowed": False, "root": str(Path(root).resolve())}


def audit_row(plan: dict, *, emitted: bool, reply_committed: bool) -> dict:
    if reply_committed and not emitted:
        raise ValueError("reply cannot claim an un-emitted action")
    return {**plan, "emitted": emitted, "reply_committed": reply_committed,
            "outcome": "reply_committed" if reply_committed else
                       "emission_unknown" if emitted else "not_emitted"}
