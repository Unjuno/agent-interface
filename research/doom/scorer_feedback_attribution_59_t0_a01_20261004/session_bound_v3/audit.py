"""Independent saved-result and source-pin audit for the A03 guard."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
DOOM = PACKAGE.parent


def audit() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    assert freeze["schema"] == "scorer-feedback-session-bound-a03-freeze-v1"
    parent_source = DOOM / freeze["parent_source"]
    parent_hash = hashlib.sha256(parent_source.read_bytes()).hexdigest()
    assert parent_hash == freeze["parent_source_sha256"]
    for relative, expected_hash in freeze["successor_sha256"].items():
        actual_hash = hashlib.sha256((DOOM / relative).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (relative, actual_hash)

    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    assert result["schema"] == "scorer-feedback-session-bound-a03-v1"
    assert result["parent_head"] == freeze["parent_head"]
    assert result["status"] == "PASS_SESSION_BOUND_A03"
    assert result["a03_unguarded_cross_session"]["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
    assert result["a03_unguarded_cross_session"]["possible_intent_tokens"] == ["intent-a"]
    assert result["a03_unguarded_cross_session"]["intent_token"] is None
    assert result["v3_cross_session"]["disposition"] == "REJECTED"
    assert result["v3_same_session"]["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
    assert result["v3_same_session"]["intent_token"] is None
    assert result["v3_same_session"]["causal_attribution"] == "NOT_ESTABLISHED"
    assert result["v3_endpoint_tie"]["status"] == "UNRESOLVED"
    assert result["v3_missing_identity"]["disposition"] == "REJECTED"

    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected_hash, relative = line.split(None, 1)
        relative = relative.strip()
        assert not relative.startswith("/") and ".." not in Path(relative).parts
        actual_hash = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (relative, actual_hash)
    return {
        "schema": "scorer-feedback-session-bound-a03-audit-v1",
        "status": "PASS_SESSION_BOUND_A03",
        "checks": ["frozen A03 source hash", "successor source hashes", "cross-session refusal", "A03 label semantics preserved", "endpoint tie unresolved", "manifest matches"],
        "scope": "saved synthetic construction result only",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
