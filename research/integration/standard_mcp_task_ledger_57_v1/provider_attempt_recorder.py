"""Durable call-boundary receipts for the standard-MCP task ledger.

This module wraps an injected provider callable; it does not select or invoke a
provider itself. Use one private, exclusively owned directory per task run.
"""

import asyncio
import hashlib
import json
import os
import re
import threading
import time
import uuid
from pathlib import Path, PurePosixPath

from ledger import LedgerValidationError, _ATTEMPT_STATUSES, _HASH, _validate_usage


class AttemptJournalError(ValueError):
    """The durable attempt journal is malformed or its raw evidence drifted."""


class IncompleteProviderAttemptError(AttemptJournalError):
    """At least one provider call was started without a durable terminal row."""


_ATTEMPT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SCORER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SESSION_ID = re.compile(r"^[0-9a-f]{32}$")
_UNAVAILABLE_USAGE = {
    "status": "unavailable",
    "input_tokens": None,
    "output_tokens": None,
}


class ProviderAttemptRecorder:
    """Persist raw request/response bytes and reconcile attempts conservatively.

    ``provider_call`` returns a mapping with ``status``, ``usage`` and optional
    ``response_bytes``. The start row and request bytes are fsynced before the
    callable runs. A timeout or exception is retained with unavailable usage and
    then re-raised to preserve the provider's ordinary control flow.
    """

    def __init__(self, root, *, clock_ns=time.monotonic_ns):
        self.root = Path(root).resolve()
        self.raw_root = self.root / "raw"
        self.journal_path = self.root / "attempts.jsonl"
        self.clock_ns = clock_ns
        self.session_id = uuid.uuid4().hex
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.raw_root.mkdir(exist_ok=True)
        except OSError as exc:
            raise AttemptJournalError("raw evidence directory is unavailable") from exc
        self._assert_raw_root()

    def begin(self, attempt_id, request_bytes):
        """Durably record a provider attempt before its call can begin."""
        if not isinstance(attempt_id, str) or not _ATTEMPT_ID.fullmatch(attempt_id):
            raise AttemptJournalError("attempt id must be a safe path component")
        if not isinstance(request_bytes, bytes):
            raise AttemptJournalError("request evidence must be raw bytes")

        with self._lock:
            current = self.reconcile(allow_incomplete=True)
            if any(event["kind"] == "task_score" for event in current["events"]):
                raise AttemptJournalError("independent task score is terminal")
            if (current["unresolved_attempt_ids"] or
                    current["unresolved_tool_call_ids"]):
                rows = self._read_rows()
                unresolved_attempts = set(current["unresolved_attempt_ids"])
                unresolved_calls = set(current["unresolved_tool_call_ids"])
                if any(
                        row["session_id"] != self.session_id
                        for row in rows
                        if (row["event"] == "model_attempt_started" and
                            row["attempt_id"] in unresolved_attempts) or
                           (row["event"] == "tool_call_started" and
                            row["call_id"] in unresolved_calls)):
                    raise IncompleteProviderAttemptError(
                        "an unfinished operation belongs to another recorder session")
            if (attempt_id in current["unresolved_attempt_ids"] or
                    any(event.get("attempt_id") == attempt_id
                        for event in current["events"])):
                raise AttemptJournalError("attempt id has already been used")

            started_ns = self._now()
            request_ref = self._write_raw(attempt_id, "request", request_bytes)
            self._append({
                "event": "model_attempt_started",
                "attempt_id": attempt_id,
                "session_id": self.session_id,
                "started_ns": started_ns,
                "request_ref": request_ref,
            })
            return started_ns

    def finish(self, attempt_id, *, status, usage, ended_ns=None,
               response_bytes=None):
        """Persist one terminal provider outcome for a prior durable start."""
        if status not in _ATTEMPT_STATUSES:
            raise AttemptJournalError("unknown provider attempt status")
        try:
            _validate_usage(usage)
        except LedgerValidationError as exc:
            raise AttemptJournalError("provider usage is not normalized") from exc
        if response_bytes is not None and not isinstance(response_bytes, bytes):
            raise AttemptJournalError("response evidence must be raw bytes or null")

        with self._lock:
            current = self.reconcile(allow_incomplete=True)
            starts = [row for row in self._read_rows()
                      if row["event"] == "model_attempt_started"]
            start = next((row for row in starts
                          if row["attempt_id"] == attempt_id), None)
            if start is None:
                raise AttemptJournalError("cannot finish an unstarted attempt")
            if start.get("session_id") != self.session_id:
                raise IncompleteProviderAttemptError(
                    "cannot finish an attempt from another recorder session")
            if attempt_id not in current["unresolved_attempt_ids"]:
                raise AttemptJournalError("attempt already has a terminal outcome")

            ended_ns = self._now() if ended_ns is None else ended_ns
            if type(ended_ns) is not int or ended_ns < start["started_ns"]:
                raise AttemptJournalError("attempt end must follow its start")
            response_ref = (None if response_bytes is None else
                            self._write_raw(attempt_id, "response", response_bytes))
            self._append({
                "event": "model_attempt_finished",
                "attempt_id": attempt_id,
                "session_id": self.session_id,
                "ended_ns": ended_ns,
                "status": status,
                "usage": usage,
                "response_ref": response_ref,
            })

    def invoke(self, attempt_id, request_bytes, provider_call):
        """Record a call, including thrown failures, and return its raw result."""
        self.begin(attempt_id, request_bytes)
        try:
            result = provider_call()
        except BaseException as exc:
            status = self._exception_status(exc)
            self.finish(attempt_id, status=status, usage=_UNAVAILABLE_USAGE)
            raise

        return self._record_provider_result(attempt_id, result)

    async def invoke_async(self, attempt_id, request_bytes, provider_call):
        """Durably wrap an awaited provider call, including task cancellation."""
        self.begin(attempt_id, request_bytes)
        try:
            result = await provider_call()
        except BaseException as exc:
            self.finish(attempt_id, status=self._exception_status(exc),
                        usage=_UNAVAILABLE_USAGE)
            raise

        return self._record_provider_result(attempt_id, result)

    def _record_provider_result(self, attempt_id, result):
        response_bytes = None
        if isinstance(result, dict) and isinstance(result.get("response_bytes"), bytes):
            response_bytes = result["response_bytes"]
        status = result.get("status") if isinstance(result, dict) else None
        usage = result.get("usage") if isinstance(result, dict) else None
        try:
            if status not in _ATTEMPT_STATUSES:
                raise AttemptJournalError("provider result has no valid terminal status")
            _validate_usage(usage)
        except LedgerValidationError as exc:
            status = "malformed"
            usage = _UNAVAILABLE_USAGE
        except AttemptJournalError:
            status = "malformed"
            usage = _UNAVAILABLE_USAGE
        self.finish(attempt_id, status=status, usage=usage,
                    response_bytes=response_bytes)
        return result

    @staticmethod
    def _exception_status(exc):
        if isinstance(exc, TimeoutError):
            return "timeout"
        if isinstance(exc, (KeyboardInterrupt, asyncio.CancelledError)):
            return "cancelled"
        return "failed"

    def begin_tool_call(self, attempt_id, call_id, method, request_bytes):
        """Persist one MCP call admission before invoking the transport."""
        if attempt_id is not None and (
                not isinstance(attempt_id, str) or
                not _ATTEMPT_ID.fullmatch(attempt_id)):
            raise AttemptJournalError(
                "model attempt id must be a safe path component or null")
        if not isinstance(call_id, str) or not _ATTEMPT_ID.fullmatch(call_id):
            raise AttemptJournalError("MCP call id must be a safe path component")
        if not isinstance(method, str) or not method:
            raise AttemptJournalError("MCP method name is required")
        if not isinstance(request_bytes, bytes):
            raise AttemptJournalError("MCP request evidence must be raw bytes")

        with self._lock:
            current = self.reconcile(allow_incomplete=True)
            if any(event["kind"] == "task_score" for event in current["events"]):
                raise AttemptJournalError("independent task score is terminal")
            parent = (next((event for event in current["events"]
                            if event["kind"] == "model_attempt" and
                            event["attempt_id"] == attempt_id), None)
                      if attempt_id is not None else None)
            if attempt_id is not None and (
                    parent is None or parent["session_id"] != self.session_id or
                    parent["status"] != "completed"):
                raise AttemptJournalError(
                    "MCP calls require a completed provider generation in this session")
            if (call_id in current["unresolved_tool_call_ids"] or
                    any(event.get("call_id") == call_id for event in current["events"])):
                raise AttemptJournalError("MCP call id has already been used")
            started_ns = self._now()
            if parent is not None and started_ns < parent["ended_ns"]:
                raise AttemptJournalError("MCP call must start after provider completion")
            raw_id = self._tool_raw_id(attempt_id, call_id)
            request_ref = self._write_raw(raw_id, "tool-request", request_bytes)
            self._append({
                "event": "tool_call_started",
                "attempt_id": attempt_id,
                "session_id": self.session_id,
                "call_id": call_id,
                "method": method,
                "started_ns": started_ns,
                "request_ref": request_ref,
            })
            return started_ns

    def invoke_tool(self, attempt_id, call_id, method, request_bytes, tool_call):
        """Durably wrap an MCP call; the callback returns result plus raw bytes.

        The callback returns ``{"result": <dict>, "response_bytes": <bytes|null>}``.
        Bytes must be the captured MCP response representation when raw response
        custody is claimed.
        """
        self.begin_tool_call(attempt_id, call_id, method, request_bytes)

        try:
            adapter_result = tool_call()
        except BaseException as exc:
            self.finish_tool_call(
                attempt_id, call_id,
                result={"status": "raised", "exception_type": type(exc).__name__},
            )
            raise

        if (not isinstance(adapter_result, dict) or
                not isinstance(adapter_result.get("result"), dict) or
                (adapter_result.get("response_bytes") is not None and
                 not isinstance(adapter_result.get("response_bytes"), bytes))):
            self.finish_tool_call(
                attempt_id, call_id,
                result={"status": "malformed", "error_type": "adapter_result"},
            )
            raise AttemptJournalError("MCP adapter result is malformed")
        self.finish_tool_call(
            attempt_id, call_id,
            result=adapter_result["result"],
            response_bytes=adapter_result.get("response_bytes"),
        )
        return adapter_result["result"]

    async def invoke_tool_async(self, attempt_id, call_id, method, request_bytes,
                                tool_call):
        """Durably wrap an awaited MCP call and preserve cancellation/errors."""
        self.begin_tool_call(attempt_id, call_id, method, request_bytes)
        try:
            adapter_result = await tool_call()
        except BaseException as exc:
            self.finish_tool_call(
                attempt_id, call_id,
                result={"status": "raised", "exception_type": type(exc).__name__},
            )
            raise

        if (not isinstance(adapter_result, dict) or
                not isinstance(adapter_result.get("result"), dict) or
                (adapter_result.get("response_bytes") is not None and
                 not isinstance(adapter_result.get("response_bytes"), bytes))):
            self.finish_tool_call(
                attempt_id, call_id,
                result={"status": "malformed", "error_type": "adapter_result"},
            )
            raise AttemptJournalError("MCP adapter result is malformed")
        self.finish_tool_call(
            attempt_id, call_id,
            result=adapter_result["result"],
            response_bytes=adapter_result.get("response_bytes"),
        )
        return adapter_result["result"]

    def finish_tool_call(self, attempt_id, call_id, *, result,
                         response_bytes=None, ended_ns=None):
        """Durably finish a standard-MCP call begun by ``invoke_tool``."""
        if not isinstance(result, dict):
            raise AttemptJournalError("MCP result must be an object")
        try:
            json.dumps(result, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise AttemptJournalError("MCP result is not JSON serializable") from exc
        if response_bytes is not None and not isinstance(response_bytes, bytes):
            raise AttemptJournalError("MCP response evidence must be raw bytes or null")

        with self._lock:
            current = self.reconcile(allow_incomplete=True)
            row = next((item for item in self._read_rows()
                        if item["event"] == "tool_call_started" and
                        item["call_id"] == call_id), None)
            if row is None or row["attempt_id"] != attempt_id:
                raise AttemptJournalError("cannot finish an unstarted MCP call")
            if row["session_id"] != self.session_id:
                raise IncompleteProviderAttemptError(
                    "cannot finish an MCP call from another recorder session")
            if call_id not in current["unresolved_tool_call_ids"]:
                raise AttemptJournalError("MCP call already has a terminal outcome")
            ended_ns = self._now() if ended_ns is None else ended_ns
            if type(ended_ns) is not int or ended_ns < row["started_ns"]:
                raise AttemptJournalError("MCP call end must follow its start")
            response_ref = (None if response_bytes is None else
                            self._write_raw(self._tool_raw_id(attempt_id, call_id),
                                            "tool-response", response_bytes))
            self._append({
                "event": "tool_call_finished",
                "attempt_id": attempt_id,
                "session_id": self.session_id,
                "call_id": call_id,
                "ended_ns": ended_ns,
                "result": result,
                "response_ref": response_ref,
            })

    def record_task_score(self, scorer_id, task_success, state_bytes):
        """Append one terminal independent-score certificate and raw state.

        Independence is asserted by the caller, not established by this
        recorder. ``state_bytes`` must be the scorer's canonical final-state
        evidence, separate from the runtime method result.
        """
        if not isinstance(scorer_id, str) or not _SCORER_ID.fullmatch(scorer_id):
            raise AttemptJournalError("scorer id is missing or malformed")
        if type(task_success) not in (bool, type(None)):
            raise AttemptJournalError("task score must be true, false, or unknown")
        if not isinstance(state_bytes, bytes) or not state_bytes:
            raise AttemptJournalError("independent state evidence must be nonempty bytes")

        with self._lock:
            current = self.reconcile()
            if any(event["kind"] == "task_score" for event in current["events"]):
                raise AttemptJournalError("independent task score is already recorded")
            last_end = max((event["ended_ns"] for event in current["events"]),
                           default=-1)
            observed_ns = self._now()
            if observed_ns < last_end:
                raise AttemptJournalError(
                    "independent score must follow all recorded operations")
            state_ref = self._write_raw("task-score", "state", state_bytes)
            self._append({
                "event": "task_score_recorded",
                "session_id": self.session_id,
                "scorer_id": scorer_id,
                "independent": True,
                "task_success": task_success,
                "started_ns": observed_ns,
                "ended_ns": observed_ns,
                "state_ref": state_ref,
            })
            return state_ref

    def reconcile(self, *, allow_incomplete=False):
        """Return ledger events and verified raw refs, or fail closed."""
        with self._lock:
            rows = self._read_rows()
            starts, finished, model_order = {}, {}, []
            tool_starts, tool_finished, tool_order = {}, {}, []
            previous_started_ns = -1
            latest_ended_ns = -1
            task_score_row = None
            for row in rows:
                event = row.get("event")
                attempt_id = row.get("attempt_id")
                if task_score_row is not None:
                    raise AttemptJournalError("task score must be the terminal journal event")
                valid_attempt_id = (isinstance(attempt_id, str) and
                                    _ATTEMPT_ID.fullmatch(attempt_id))
                if ((event in ("model_attempt_started", "model_attempt_finished")
                     and not valid_attempt_id) or
                    (event in ("tool_call_started", "tool_call_finished") and
                     attempt_id is not None and not valid_attempt_id) or
                    (event == "task_score_recorded" and attempt_id is not None)):
                    raise AttemptJournalError("journal row has an invalid attempt id")
                if event == "model_attempt_started":
                    if attempt_id in starts:
                        raise AttemptJournalError("duplicate provider attempt start")
                    session_id = row.get("session_id")
                    if not isinstance(session_id, str) or not _SESSION_ID.fullmatch(
                            session_id):
                        raise AttemptJournalError("provider recorder session is invalid")
                    self._verify_raw_ref(row.get("request_ref"))
                    started_ns = row.get("started_ns")
                    if (type(started_ns) is not int or started_ns < 0 or
                            started_ns < previous_started_ns):
                        raise AttemptJournalError("provider start time is invalid")
                    previous_started_ns = started_ns
                    starts[attempt_id] = row
                    model_order.append(attempt_id)
                elif event == "model_attempt_finished":
                    if attempt_id not in starts or attempt_id in finished:
                        raise AttemptJournalError("orphan or duplicate provider terminal")
                    if row.get("session_id") != starts[attempt_id]["session_id"]:
                        raise AttemptJournalError("provider terminal has a different session")
                    ended_ns = row.get("ended_ns")
                    if type(ended_ns) is not int or ended_ns < starts[attempt_id][
                            "started_ns"]:
                        raise AttemptJournalError("provider end time is invalid")
                    latest_ended_ns = max(latest_ended_ns, ended_ns)
                    if row.get("status") not in _ATTEMPT_STATUSES:
                        raise AttemptJournalError("provider terminal status is invalid")
                    try:
                        _validate_usage(row.get("usage"))
                    except LedgerValidationError as exc:
                        raise AttemptJournalError("provider terminal usage is invalid") from exc
                    response_ref = row.get("response_ref")
                    if response_ref is not None:
                        self._verify_raw_ref(response_ref)
                    finished[attempt_id] = row
                elif event == "tool_call_started":
                    call_id = row.get("call_id")
                    if (not isinstance(call_id, str) or
                            not _ATTEMPT_ID.fullmatch(call_id) or
                            call_id in tool_starts):
                        raise AttemptJournalError("MCP call id is invalid or duplicated")
                    if attempt_id is None:
                        if (not isinstance(row.get("session_id"), str) or
                                not _SESSION_ID.fullmatch(row["session_id"])):
                            raise AttemptJournalError(
                                "unlinked MCP call recorder session is invalid")
                        parent = None
                    else:
                        parent = finished.get(attempt_id)
                        if (parent is None or parent["status"] != "completed" or
                                row.get("session_id") != starts[attempt_id]["session_id"]):
                            raise AttemptJournalError(
                                "MCP call is not linked to a completed provider generation")
                    if not isinstance(row.get("method"), str) or not row["method"]:
                        raise AttemptJournalError("MCP call method is missing")
                    started_ns = row.get("started_ns")
                    if (type(started_ns) is not int or
                            (parent is not None and started_ns < parent["ended_ns"]) or
                            started_ns < previous_started_ns):
                        raise AttemptJournalError("MCP call start time is invalid")
                    previous_started_ns = started_ns
                    self._verify_raw_ref(row.get("request_ref"))
                    tool_starts[call_id] = row
                    tool_order.append(call_id)
                elif event == "tool_call_finished":
                    call_id = row.get("call_id")
                    start = tool_starts.get(call_id)
                    if start is None or call_id in tool_finished:
                        raise AttemptJournalError("orphan or duplicate MCP call terminal")
                    if (row.get("attempt_id") != start["attempt_id"] or
                            row.get("session_id") != start["session_id"]):
                        raise AttemptJournalError("MCP call terminal changed its owner")
                    ended_ns = row.get("ended_ns")
                    if type(ended_ns) is not int or ended_ns < start["started_ns"]:
                        raise AttemptJournalError("MCP call end time is invalid")
                    latest_ended_ns = max(latest_ended_ns, ended_ns)
                    if not isinstance(row.get("result"), dict):
                        raise AttemptJournalError("MCP call result must be an object")
                    try:
                        json.dumps(row["result"], sort_keys=True,
                                   separators=(",", ":"))
                    except (TypeError, ValueError) as exc:
                        raise AttemptJournalError(
                            "MCP call result is not JSON serializable") from exc
                    response_ref = row.get("response_ref")
                    if response_ref is not None:
                        self._verify_raw_ref(response_ref)
                    tool_finished[call_id] = row
                elif event == "task_score_recorded":
                    session_id = row.get("session_id")
                    scorer_id = row.get("scorer_id")
                    task_success = row.get("task_success")
                    started_ns = row.get("started_ns")
                    ended_ns = row.get("ended_ns")
                    if (not isinstance(session_id, str) or
                            not _SESSION_ID.fullmatch(session_id) or
                            not isinstance(scorer_id, str) or
                            not _SCORER_ID.fullmatch(scorer_id) or
                            row.get("independent") is not True or
                            type(task_success) not in (bool, type(None))):
                        raise AttemptJournalError("independent task score is malformed")
                    if (type(started_ns) is not int or type(ended_ns) is not int or
                            started_ns < latest_ended_ns or ended_ns < started_ns or
                            started_ns < previous_started_ns):
                        raise AttemptJournalError(
                            "independent score must follow recorded operations")
                    state_ref = row.get("state_ref")
                    self._verify_raw_ref(state_ref)
                    task_score_row = row
                    previous_started_ns = started_ns
                else:
                    raise AttemptJournalError("unknown provider journal event")

            unresolved_attempts = [attempt_id for attempt_id in model_order
                                   if attempt_id not in finished]
            unresolved_tool_calls = [call_id for call_id in tool_order
                                     if call_id not in tool_finished]
            if task_score_row is not None and (unresolved_attempts or
                                               unresolved_tool_calls):
                raise AttemptJournalError(
                    "independent task score cannot follow unresolved operations")
            if (unresolved_attempts or unresolved_tool_calls) and not allow_incomplete:
                pending = (["model:" + item for item in unresolved_attempts] +
                           ["tool:" + item for item in unresolved_tool_calls])
                raise IncompleteProviderAttemptError(
                    "operations lack terminal receipts: " + ", ".join(pending))

            ordered_events = []
            for attempt_id in model_order:
                if attempt_id not in finished:
                    continue
                start = starts[attempt_id]
                terminal = finished[attempt_id]
                refs = [start["request_ref"]]
                if terminal.get("response_ref") is not None:
                    refs.append(terminal["response_ref"])
                ordered_events.append((start["started_ns"], {
                    "kind": "model_attempt", "attempt_id": attempt_id,
                    "session_id": start["session_id"], "status": terminal["status"],
                    "started_ns": start["started_ns"],
                    "ended_ns": terminal["ended_ns"], "usage": terminal["usage"],
                    "response_status": ("raw_retained" if terminal.get(
                        "response_ref") is not None else "unavailable"),
                    "raw_refs": refs,
                }))

            for call_id in tool_order:
                if call_id not in tool_finished:
                    continue
                start = tool_starts[call_id]
                terminal = tool_finished[call_id]
                refs = [start["request_ref"]]
                response_ref = terminal.get("response_ref")
                response_status = "unavailable"
                if response_ref is not None:
                    refs.append(response_ref)
                    response_bytes = self._verify_raw_ref(response_ref)
                    try:
                        response_object = json.loads(response_bytes.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        response_status = "unparseable"
                    else:
                        response_status = ("matched" if response_object ==
                                           terminal["result"] else "mismatch")
                ordered_events.append((start["started_ns"], {
                    "kind": "tool_call", "call_id": call_id,
                    "model_attempt_id": start["attempt_id"],
                    "session_id": start["session_id"], "method": start["method"],
                    "started_ns": start["started_ns"],
                    "ended_ns": terminal["ended_ns"], "result": terminal["result"],
                    "response_status": response_status, "raw_refs": refs,
                }))

            if task_score_row is not None:
                state_ref = task_score_row["state_ref"]
                ordered_events.append((task_score_row["started_ns"], {
                    "kind": "task_score",
                    "session_id": task_score_row["session_id"],
                    "started_ns": task_score_row["started_ns"],
                    "ended_ns": task_score_row["ended_ns"],
                    "independent": True,
                    "scorer_id": task_score_row["scorer_id"],
                    "task_success": task_score_row["task_success"],
                    "state_sha256": state_ref["sha256"],
                    "raw_refs": [state_ref],
                }))

            ordered_events.sort(key=lambda pair: pair[0])
            events = []
            raw_refs = []
            for seq, (_, event) in enumerate(ordered_events, start=1):
                event["seq"] = seq
                events.append(event)
                raw_refs.extend(event["raw_refs"])
            return {
                "complete": not unresolved_attempts and not unresolved_tool_calls,
                "events": events,
                "raw_refs": raw_refs,
                "unresolved_attempt_ids": unresolved_attempts,
                "unresolved_tool_call_ids": unresolved_tool_calls,
            }

    def _now(self):
        value = self.clock_ns()
        if type(value) is not int or value < 0:
            raise AttemptJournalError("monotonic clock must return a nonnegative int")
        return value

    def _write_raw(self, attempt_id, kind, content):
        self._assert_raw_root()
        relative = f"raw/{attempt_id}.{kind}.bin"
        path = self.root / PurePosixPath(relative)
        digest = hashlib.sha256(content).hexdigest()
        try:
            with path.open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise AttemptJournalError("raw attempt file already exists") from exc
        return {"path": relative, "sha256": digest}

    @staticmethod
    def _tool_raw_id(attempt_id, call_id):
        """Bound MCP raw filenames independently of user-controlled ID length."""
        identity = "" if attempt_id is None else attempt_id
        digest = hashlib.sha256(
            (identity + "\0" + call_id).encode("utf-8")).hexdigest()
        return "tool-" + digest

    def _assert_raw_root(self):
        try:
            resolved = self.raw_root.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise AttemptJournalError("raw evidence directory cannot be resolved") from exc
        expected = os.path.normcase(os.path.normpath(str(self.raw_root.absolute())))
        actual = os.path.normcase(os.path.normpath(str(resolved)))
        if actual != expected or resolved.parent != self.root:
            raise AttemptJournalError(
                "raw evidence directory must remain a direct child of the run directory")

    def _verify_raw_ref(self, raw_ref):
        if not isinstance(raw_ref, dict):
            raise AttemptJournalError("provider journal has no raw reference")
        relative = raw_ref.get("path")
        digest = raw_ref.get("sha256")
        if not isinstance(relative, str) or "\\" in relative:
            raise AttemptJournalError("provider raw path is invalid")
        parsed = PurePosixPath(relative)
        if (parsed.is_absolute() or len(parsed.parts) != 2 or parsed.parts[0] != "raw"
                or parsed.as_posix() != relative
                or any(part in ("", ".", "..") for part in parsed.parts)):
            raise AttemptJournalError("provider raw path is not normalized")
        path = (self.root / parsed).resolve()
        if self.root not in path.parents:
            raise AttemptJournalError("provider raw path escaped the run directory")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AttemptJournalError("provider raw digest is invalid")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise AttemptJournalError("provider raw evidence is missing") from exc
        if hashlib.sha256(content).hexdigest() != digest:
            raise AttemptJournalError("provider raw evidence digest does not match")
        return content

    def _read_rows(self):
        if not self.journal_path.exists():
            return []
        rows = []
        try:
            with self.journal_path.open("r", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, start=1):
                    if not line.endswith("\n"):
                        raise AttemptJournalError("journal ends with a partial row")
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise AttemptJournalError("journal row must be an object")
                    rows.append(row)
        except (OSError, json.JSONDecodeError) as exc:
            raise AttemptJournalError("provider journal cannot be read") from exc
        return rows

    def _append(self, row):
        encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8")
        with self.journal_path.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
