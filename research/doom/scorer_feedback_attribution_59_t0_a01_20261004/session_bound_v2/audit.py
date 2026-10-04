"""Independent fixed-result/source-pin audit for the session-bound T0."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
def audit() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    assert freeze["schema"] == "scorer-feedback-session-bound-freeze-v1"
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    assert result["schema"] == "scorer-feedback-session-bound-t0-v2"
    assert result["parent_head"] == freeze["parent_head"]
    assert result["status"] == "PASS_SESSION_BOUND"
    assert result["v1_cross_session_control"]["status"] == "TEMPORALLY_UNIQUE"
    assert result["v1_cross_session_control"]["intent_token"] == "intent-a"
    assert result["v2_cross_session"]["disposition"] == "REJECTED"
    assert result["v2_same_session"]["status"] == "TEMPORALLY_UNIQUE"
    assert result["v2_same_session"]["causal_attribution"] == "NOT_ESTABLISHED"
    assert result["v2_missing_session"]["disposition"] == "REJECTED"

    parent_candidate = PACKAGE / "scorer_feedback_attribution_v1.py"
    parent_sha = hashlib.sha256(parent_candidate.read_bytes()).hexdigest()
    assert parent_sha == "3f9b8712526c16fded9809d91dfb2e76f935cc5625ab07e297ef69d6f7ce745b"
    for relative, expected_sha in freeze["successor_sha256"].items():
        actual_sha = hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()
        assert actual_sha == expected_sha, (relative, actual_sha)
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected_sha, relative = line.split(None, 1)
        relative = relative.strip()
        assert not relative.startswith("/") and ".." not in Path(relative).parts
        actual_sha = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        assert actual_sha == expected_sha, (relative, actual_sha)
    return {
        "schema": "scorer-feedback-session-bound-audit-v1",
        "status": "PASS_SESSION_BOUND",
        "checks": [
            "frozen parent implementation hash",
            "result records v1 cross-session false join",
            "result records v2 cross-session and missing-ID refusal",
            "same-session association remains explicitly non-causal",
            "candidate, test, and runner match frozen successor files",
            "all FILES.sha256 members match",
        ],
        "scope": "saved synthetic construction result; no live session was audited",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
