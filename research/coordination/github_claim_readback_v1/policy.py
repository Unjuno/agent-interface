#!/usr/bin/env python3
"""Pure readback classifier for lost-response claim registration.

No GitHub access and no write capability. The caller must provide the candidate
claim and exactly one claim observed from a fresh register GET.
"""

CANONICAL_FIELDS = (
    "owner_nonce",
    "task_id",
    "scope",
    "successor",
    "question_key",
)


def canonical(claim):
    return tuple(claim[k] for k in CANONICAL_FIELDS)


def classify(candidate, observed):
    if canonical(candidate) == canonical(observed):
        return "ALREADY_REGISTERED_SELF"
    if candidate["owner_nonce"] == observed["owner_nonce"]:
        return "CONFLICT_CONTENT_MISMATCH"
    if (
        candidate["successor"] == observed["successor"]
        and candidate["question_key"] == observed["question_key"]
    ):
        return "CONFLICT_OTHER_OWNER"
    return "UNRELATED_EXISTING_CLAIM"
