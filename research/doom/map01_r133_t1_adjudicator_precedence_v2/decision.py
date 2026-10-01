"""Candidate paired-decision and identity-validation contract for #5658."""

from __future__ import annotations

import re

FIELDS = ("model_contract_sha256", "fixture_sha256", "decision_contract_sha256")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SIGNS = (-1, 0, 1)


def classify(progress: tuple[int, int, int], exposure: tuple[int, int, int]) -> str:
    if any(x not in SIGNS for x in progress + exposure):
        raise ValueError("sign_out_of_domain")
    if any(x < 0 for x in progress) or any(x > 0 for x in exposure):
        return "FAIL_DIRECTIONAL"
    if all(x >= 0 for x in progress) and any(x > 0 for x in progress) and all(x <= 0 for x in exposure) and any(x < 0 for x in exposure):
        return "PASS_DIRECTIONAL"
    return "UNCERTAIN"


def validate_identities(rows: list[dict[str, str]]) -> str:
    if len(rows) < 2:
        return "identity_missing:session_pair"
    for field in FIELDS:
        if any(field not in row for row in rows):
            return f"identity_missing:{field}"
    for row in rows:
        for field in FIELDS:
            if not isinstance(row[field], str) or HEX64.fullmatch(row[field]) is None:
                return f"identity_format:{field}"
    for field in FIELDS:
        if len({row[field] for row in rows}) != 1:
            return f"identity_mismatch:{field}"
    return "IDENTITY_OK"
