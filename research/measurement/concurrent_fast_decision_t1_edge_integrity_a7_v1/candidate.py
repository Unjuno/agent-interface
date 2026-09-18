from __future__ import annotations
ALLOWED = ("ADVANCE", "WATCH", "YIELD")
_MAPPING = {
    "CLEAR_PROGRESS": "ADVANCE",
    "UNCERTAIN_TRANSIENT": "WATCH",
    "HARD_INVALIDATION": "YIELD",
}
def select_disposition(state: str) -> str:
    out = _MAPPING.get(state)
    if out is None:
        raise ValueError("unknown typed local state")
    if out not in ALLOWED:
        raise RuntimeError("out-of-envelope disposition")
    return out
