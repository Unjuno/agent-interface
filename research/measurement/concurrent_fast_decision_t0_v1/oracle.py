from __future__ import annotations

_ORACLE = {
    "CLEAR_PROGRESS": "ADVANCE",
    "UNCERTAIN_TRANSIENT": "WATCH",
    "HARD_INVALIDATION": "YIELD",
}

def expected_disposition(state: str) -> str:
    if state not in _ORACLE:
        raise ValueError("unknown oracle state")
    return _ORACLE[state]
