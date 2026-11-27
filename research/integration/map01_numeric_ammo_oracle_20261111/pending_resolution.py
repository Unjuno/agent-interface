"""Deadline-derived pending-result wait for bounded Win32 trial runners.

This is trial infrastructure, not a runtime custody authority. It never sends
cancel, replay, close, or input operations. On timeout it atomically preserves
the poll history and exact serialized expiry before raising.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time

from .input_boundary import audit_expiry_key_release


class PendingResolutionTimeout(TimeoutError):
    def __init__(self, receipt: dict):
        super().__init__("pending result remained nonterminal through its derived bound")
        self.receipt = receipt


class PendingResolutionProtocolError(RuntimeError):
    def __init__(self, receipt: dict):
        super().__init__("pending result query returned a different call ID")
        self.receipt = receipt


def resolver_deadline_ns(submission: dict, *, cleanup_ns: int,
                         horizon_ns: int, margin_ns: int) -> int:
    """Return actual serialized expiry + recovery + full horizon + margin."""
    if type(submission) is not dict:
        raise ValueError("serialized submission must be an object")
    program = submission.get("program")
    authority = program.get("authority") if type(program) is dict else None
    expiry = authority.get("expires_at_ns") if type(authority) is dict else None
    if type(expiry) is not int or expiry <= 0:
        raise ValueError("serialized program expiry is missing or invalid")
    budgets = (cleanup_ns, horizon_ns, margin_ns)
    if any(type(value) is not int or value < 0 for value in budgets):
        raise ValueError("resolver budgets must be nonnegative integers")
    if horizon_ns <= 0:
        raise ValueError("a positive post-release horizon is required")
    deadline = expiry + sum(budgets)
    if deadline <= expiry:  # defensive against integer/representation changes
        raise ValueError("resolver deadline overflow")
    return deadline


def load_serialized_submission(path) -> dict:
    """Load the exact frozen public-dispatch request from its evidence file."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("serialized action submission is unavailable") from error
    if type(value) is not dict or type(value.get("program")) is not dict:
        raise ValueError("serialized action submission has no program object")
    # Validate the lease before returning the object to either timing consumer.
    resolver_deadline_ns(value, cleanup_ns=0, horizon_ns=1, margin_ns=0)
    return value


def audit_boundary_from_submission(samples, submission, *, max_bracket_ns=20_000_000):
    """Audit expiry using only the deadline in the serialized submission."""
    expiry = submission["program"]["authority"]["expires_at_ns"]
    return audit_expiry_key_release(samples, expiry,
        max_bracket_ns=max_bracket_ns)


def resolve_trial_and_audit(call_id: str, submission_path, query, samples, *,
                            pending_receipt_path, boundary_receipt_path,
                            **wait_options):
    """Trial-runner seam: resolve exact call, then persist submitted-expiry audit.

    The key sampler is stopped by the caller before this function is invoked.
    Boundary evidence is saved both after a terminal receipt and when pending
    resolution times out or returns a mismatched call ID.
    """
    submission = load_serialized_submission(submission_path)
    try:
        pending = wait_for_terminal(call_id, submission, query,
            receipt_path=pending_receipt_path, **wait_options)
    except (PendingResolutionTimeout, PendingResolutionProtocolError):
        boundary = audit_boundary_from_submission(samples, submission)
        _atomic_json(Path(boundary_receipt_path), boundary)
        raise
    boundary = audit_boundary_from_submission(samples, submission)
    _atomic_json(Path(boundary_receipt_path), boundary)
    return {"pending_result": pending, "expiry_boundary": boundary}


def build_compiled_pending_resolver(submission_path, query, *, receipt_path,
                                    poll_observer=None, normalize=None,
                                    **wait_options):
    """Build the ``resolve_pending(call_id, initial_reply)`` callback expected
    by ``run_public_compiled``. The initial reply is deliberately not trusted
    for identity or terminal status; every poll joins the exact call ID.
    """
    submission=load_serialized_submission(submission_path)
    if (not callable(query)
            or (normalize is not None and not callable(normalize))):
        raise ValueError("exact-call query and optional normalizer are required")

    def resolve_pending(call_id, _initial_reply):
        latest=[]
        def exact_query(requested_call_id):
            raw=query(requested_call_id)
            if type(raw) is dict:
                latest[:] = [raw]
            return normalize(raw) if normalize is not None else raw
        receipt=wait_for_terminal(call_id, submission, exact_query,
            receipt_path=receipt_path, poll_observer=poll_observer,
            **wait_options)
        return latest[-1] if receipt["terminal"] and latest else None

    return resolve_pending


def _atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
        dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def wait_for_terminal(call_id: str, submission: dict, query, *, receipt_path,
                      now_ns=time.monotonic_ns, sleep=time.sleep,
                      poll_observer=None,
                      poll_interval_ns=100_000_000, cleanup_ns=3_000_000_000,
                      horizon_ns=2_000_000_000, margin_ns=1_000_000_000,
                      terminal_statuses=("completed", "recovered", "unknown")):
    """Poll one exact call until terminal or derived deadline; never cancel it."""
    if type(call_id) is not str or not call_id:
        raise ValueError("exact call ID is required")
    if (not callable(query) or not callable(now_ns) or not callable(sleep)
            or (poll_observer is not None and not callable(poll_observer))):
        raise ValueError("query and clock functions are required")
    if type(poll_interval_ns) is not int or poll_interval_ns <= 0:
        raise ValueError("poll interval must be positive")
    deadline = resolver_deadline_ns(submission, cleanup_ns=cleanup_ns,
        horizon_ns=horizon_ns, margin_ns=margin_ns)
    history = []
    last = None
    while True:
        observed_ns = now_ns()
        if type(observed_ns) is not int or observed_ns < 0:
            raise ValueError("monotonic clock returned an invalid value")
        if last is not None and observed_ns >= deadline:
            break
        query_error = None
        observed_call_id = None
        try:
            row = query(call_id)
        except Exception as error:
            row = None
            query_error = type(error).__name__
        after_query_ns = now_ns()
        if query_error is None and type(row) is dict:
            observed_call_id = row.get("call_id")
        if query_error is None and (type(row) is not dict
                or observed_call_id != call_id):
            query_error = "call_id_mismatch"
        protocol_error = query_error == "call_id_mismatch"
        if protocol_error:
            row = None
        if query_error is None and type(row) is not dict:
            raise ValueError("pending result query did not match exact call ID")
        action = row.get("action") if type(row) is dict else None
        action_status = action.get("status") if type(action) is dict else None
        if row is not None:
            last = row
        history_row = {"observed_monotonic_ns": observed_ns,
            "query_returned_monotonic_ns": after_query_ns,
            "action_status": action_status,
            "release_confirmed": (action.get("release_confirmed")
                if type(action) is dict else None)}
        if query_error is not None:
            history_row["query_error_type"] = query_error
        if protocol_error:
            history_row["observed_call_id"] = observed_call_id
        if poll_observer is not None and query_error is None:
            try:
                annotation = poll_observer(row, observed_ns)
                if type(annotation) is not dict:
                    raise ValueError("poll observer must return an object")
                history_row["observer"] = annotation
            except Exception as error:
                history_row["observer_error_type"] = type(error).__name__
        history.append(history_row)
        receipt = {"call_id": call_id,
            "serialized_expiry_monotonic_ns": submission["program"]["authority"]["expires_at_ns"],
            "resolver_deadline_monotonic_ns": deadline,
            "cleanup_budget_ns": cleanup_ns,
            "late_input_horizon_ns": horizon_ns,
            "margin_ns": margin_ns,
            "poll_history": history,
            "terminal": action_status in terminal_statuses,
            "manual_cancel_sent": False,
            "replay": False,
            "latest_result": last}
        if protocol_error:
            receipt["stop_reason"] = "pending_result_call_id_mismatch"
            _atomic_json(Path(receipt_path), receipt)
            raise PendingResolutionProtocolError(receipt)
        _atomic_json(Path(receipt_path), receipt)
        if receipt["terminal"]:
            return receipt
        if after_query_ns >= deadline:
            break
        sleep(min(poll_interval_ns, deadline - after_query_ns) / 1_000_000_000)
    receipt["stop_reason"] = "resolver_deadline_reached_without_terminal_receipt"
    _atomic_json(Path(receipt_path), receipt)
    raise PendingResolutionTimeout(receipt)
