"""Optional session identity binding for independently emitted MAP01 records."""

import hashlib
import json


def bind_session_identity(row, session_id):
    """Return a session-bound row, or preserve the legacy row when disabled."""
    if session_id is None:
        return row
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session identity must be a nonempty string")
    if not isinstance(row, dict):
        raise TypeError("session-bound record must be a mapping")
    existing = row.get("session_id")
    if existing is not None and existing != session_id:
        raise ValueError("session identity mismatch")
    return {**row, "session_id": session_id}


def session_bound_event_sidecar(row, session_id, source_line, ordinal):
    """Bind a private record to an unchanged controller event line."""
    if session_id is None:
        return None
    if not isinstance(source_line, str):
        raise TypeError("source event must be text")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        raise ValueError("source event ordinal must be a positive integer")
    bound = bind_session_identity(row, session_id)
    bound["source_event_ordinal"] = ordinal
    bound["source_event_sha256"] = hashlib.sha256(source_line.encode("utf-8")).hexdigest()
    return bound


def encode_event_with_private_identity(row, session_id, ordinal):
    """Serialize the legacy event unchanged and return its optional private link."""
    source_line = json.dumps(row)
    return source_line, session_bound_event_sidecar(row, session_id, source_line, ordinal)
