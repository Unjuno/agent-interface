"""Capture conservative monotonic brackets around owner-issued key releases.

This module records request-call boundaries and a single shared transport sync.
It deliberately does not claim that a request was observed by the server or by
an application; callers must retain that distinction in their audit output.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping, Any


class ReleaseCaptureError(RuntimeError):
    """A release batch failed and must not be represented as successful."""

    def __init__(self, message: str, *, stage: str, completed_records=None):
        super().__init__(message)
        self.stage = stage
        self.completed_records = list(completed_records or [])


def record_release_envelopes(
    *,
    display: Any,
    owned_keys: Iterable[tuple[str, int]],
    trigger_class: str,
    owner_id: str,
    intent_token: str | None,
    reason: str,
    key_release: Callable[[Any, int], None],
    sync: Callable[[Any], None],
    clock_ns: Callable[[], int],
) -> list[dict[str, Any]]:
    """Record ordered per-key request brackets and the one shared sync return.

    An empty key set still synchronizes once, so the caller can distinguish an
    empty successful cleanup from a skipped cleanup. Any request/sync failure,
    or a non-monotonic clock bracket, raises without returning success records.
    """
    owned = tuple(owned_keys)
    if not all(isinstance(v, str) and v for v in
               (trigger_class, owner_id, reason)):
        raise ValueError("trigger, owner, and reason must be non-empty")

    pending: list[dict[str, Any]] = []
    try:
        for key, keycode in owned:
            start = clock_ns()
            key_release(display, keycode)
            returned = clock_ns()
            if returned < start:
                raise ReleaseCaptureError("inverted key-release clock bracket",
                                          stage="clock_order")
            pending.append({
                "event": "owner_key_release_bracket",
                "schema": "owner-key-release-bracket-v1",
                "owner_id": owner_id,
                "intent_token": intent_token,
                "trigger_class": trigger_class,
                "reason": reason,
                "key": key,
                "keycode": keycode,
                "request_started_ns": start,
                "request_returned_ns": returned,
                "grants_input_authority": False,
                "physical_key_up_claimed": False,
            })
        sync(display)
        sync_returned = clock_ns()
    except ReleaseCaptureError as exc:
        if not exc.completed_records:
            exc.completed_records = []
        raise
    except Exception as exc:
        stage = "sync" if len(pending) == len(owned) else "key_release"
        raise ReleaseCaptureError("release request or shared sync failed",
                                  stage=stage) from exc

    for record in pending:
        if sync_returned < record["request_returned_ns"]:
            raise ReleaseCaptureError("shared sync returned before request",
                                      stage="clock_order")
        record["shared_sync_returned_ns"] = sync_returned
    return pending
