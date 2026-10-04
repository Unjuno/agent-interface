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


class SessionBoundEventSidecar:
    """Write private identity links without propagating attribution failures."""

    def __init__(self, out_dir, session_id):
        self.out_dir = out_dir
        self.session_id = session_id
        self.event_count = 0
        self.records_written = 0
        self.failure = None

    def record(self, row, source_line, ordinal):
        if self.session_id is None:
            return
        if isinstance(ordinal, int) and not isinstance(ordinal, bool):
            self.event_count = max(self.event_count, ordinal)
        if self.failure is not None:
            return
        try:
            bound = session_bound_event_sidecar(
                row, self.session_id, source_line, ordinal
            )
            with (self.out_dir / "session-bound-events.jsonl").open(
                    "a", encoding="utf-8") as stream:
                stream.write(json.dumps(bound, sort_keys=True) + "\n")
            self.records_written += 1
        except Exception as error:
            self.failure = {
                "first_failed_ordinal": ordinal,
                "error_type": type(error).__name__,
            }

    def finalize(self):
        if self.session_id is None:
            return None
        status = {
            "schema": "session-bound-events-status-v1",
            "session_id": self.session_id,
            "event_count": self.event_count,
            "records_written": self.records_written,
            "complete": self.failure is None and self.records_written == self.event_count,
            "failure": self.failure,
        }
        try:
            (self.out_dir / "session-bound-events-status.json").write_text(
                json.dumps(status, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except Exception as error:
            status["complete"] = False
            status["status_write_error_type"] = type(error).__name__
        return status


def emit_event_row(out_dir, row, ordinal, session_sidecar, stdout_sink):
    """Publish the legacy event first; private identity failure stays nonfatal."""
    encoded = json.dumps(row)
    with (out_dir / "events.jsonl").open("a") as stream:
        stream.write(encoded + "\n")
    with (out_dir / "delivered.jsonl").open("a") as stream:
        stream.write(encoded + "\n")
    stdout_sink(encoded)
    session_sidecar.record(row, encoded, ordinal)
    return encoded
