"""Adapt one Codex App Server turn to the existing recorded public-MCP path.

The app-server client's protocol journal is the provider response artifact.
This adapter copies the bytes added by one planner turn into the per-attempt
``model/events.jsonl`` location already consumed by
``recorded_integrated_efficiency_model_call_v1``. It does not launch a model,
choose a tool, retry, or claim an upstream provider-wire capture.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time


USAGE_MAP = {
    "inputTokens": "input_tokens",
    "cachedInputTokens": "cached_input_tokens",
    "cacheWriteInputTokens": "cache_write_input_tokens",
    "outputTokens": "output_tokens",
    "reasoningOutputTokens": "reasoning_output_tokens",
}


def _turn_usage(value):
    if value is None:
        return None
    if type(value) is not dict or type(value.get("last")) is not dict:
        raise ValueError("app-server usage requires a last-turn object")
    last = value["last"]
    missing = set(USAGE_MAP) - set(last)
    if missing:
        raise ValueError("missing app-server usage fields: " + ",".join(sorted(missing)))
    result = {target: last[source] for source, target in USAGE_MAP.items()}
    if any(type(amount) is not int or amount < 0 for amount in result.values()):
        raise ValueError("usage values must be nonnegative integers")
    return result


def _partial_turn_usage(value):
    """Preserve valid known fields from an unsuccessful turn's usage record."""
    if type(value) is not dict or type(value.get("last")) is not dict:
        return None
    last = value["last"]
    return {
        target: last[source]
        for source, target in USAGE_MAP.items()
        if (source in last and type(last[source]) is int and last[source] >= 0)
    } or None


def _journal_turn_usage(response_bytes, *, thread_id, turn_id):
    """Return the newest usage update in the retained turn slice, if any."""
    updates = []
    for line in response_bytes.splitlines():
        if not line:
            continue
        row = json.loads(line)
        message = row.get("message") if isinstance(row, dict) else None
        if (row.get("direction") != "received" or not isinstance(message, dict) or
                message.get("method") != "thread/tokenUsage/updated"):
            continue
        params = message.get("params", {})
        if (isinstance(params, dict) and params.get("threadId") == thread_id and
                params.get("turnId") == turn_id):
            updates.append(params.get("tokenUsage"))
    return None if not updates else updates[-1]


def _best_effort_partial_turn_usage(response_bytes, *, thread_id, turn_id):
    """Return the latest complete usage update seen before an interrupted turn.

    A timed-out protocol stream may end with a partial JSONL record. Only
    newline-terminated records are considered, and malformed/incomplete rows
    are ignored. The result is intentionally partial: it is only the latest
    usage snapshot available at interruption, not a terminal provider total.
    """
    updates = []
    for line in response_bytes.splitlines(keepends=True):
        if not line.endswith((b"\n", b"\r")):
            continue
        try:
            row = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(row, dict):
            continue
        message = row.get("message")
        if (row.get("direction") != "received" or not isinstance(message, dict) or
                message.get("method") != "thread/tokenUsage/updated"):
            continue
        params = message.get("params", {})
        if (isinstance(params, dict) and params.get("threadId") == thread_id and
                params.get("turnId") == turn_id):
            usage = _partial_turn_usage(params.get("tokenUsage"))
            if usage:
                updates.append(usage)
    return None if not updates else updates[-1]


def _normalized_late_usage(value):
    if type(value) is not dict or type(value.get("last")) is not dict:
        raise ValueError("late app-server usage has no last-turn snapshot")
    last = value["last"]
    fields = {
        "input_tokens": "inputTokens",
        "output_tokens": "outputTokens",
        "cached_input_tokens": "cachedInputTokens",
        "cache_write_input_tokens": "cacheWriteInputTokens",
        "reasoning_output_tokens": "reasoningOutputTokens",
        "image_input_tokens": "imageInputTokens",
    }
    counts = {}
    for target, source in fields.items():
        amount = last.get(source)
        if amount is not None and (type(amount) is not int or amount < 0):
            raise ValueError("late app-server usage counters must be nonnegative integers")
        counts[target] = amount
    if all(counts[name] is not None for name in ("input_tokens", "output_tokens")):
        status = "reported"
    elif any(amount is not None for amount in counts.values()):
        status = "partial"
    else:
        raise ValueError("late app-server usage has no known counters")
    return {"status": status, **counts}


class _LateAppServerUsageSource:
    """Read only new, same-turn usage rows after caller terminalization."""

    def __init__(self, planner, handle, journal_path):
        self.planner = planner
        self.handle = handle
        self.journal_path = Path(journal_path)
        self._lock = threading.Lock()
        self._cursor = None

    def capture_terminal(self):
        """Mark the exact usage/journal boundary after the timeout is durable."""
        with self._lock:
            if self._cursor is not None:
                raise RuntimeError("late usage terminal boundary was already captured")
            cursor = self.planner.late_usage_cursor(self.handle)
            if (type(cursor) is not tuple or len(cursor) != 2 or
                    any(type(value) is not int or value < 0 for value in cursor)):
                raise RuntimeError("planner returned an invalid late usage cursor")
            self._cursor = cursor

    def read(self, timeout):
        """Return one cumulative update with its exact appended JSONL row."""
        if (type(timeout) not in (int, float) or timeout < 0 or timeout > 30):
            raise ValueError("late usage wait must be between 0 and 30 seconds")
        with self._lock:
            if self._cursor is None:
                raise RuntimeError("late usage boundary has not been captured")
            prior_count, offset = self._cursor
            received = self.planner.wait_late_usage(
                self.handle, self._cursor, timeout)
            if received is None:
                return None
            token_usage, next_count = received
            if type(next_count) is not int or next_count != prior_count + 1:
                raise RuntimeError("planner returned a non-advancing usage cursor")

            if self.journal_path.stat().st_size < offset:
                raise RuntimeError("app-server protocol journal was truncated")
            with self.journal_path.open("rb") as stream:
                stream.seek(offset)
                appended = stream.read()
            match = None
            consumed_bytes = 0
            for line in appended.splitlines(keepends=True):
                if not line.endswith((b"\n", b"\r")):
                    break
                consumed_bytes += len(line)
                try:
                    row = json.loads(line)
                except (TypeError, ValueError):
                    continue
                message = row.get("message") if isinstance(row, dict) else None
                if (not isinstance(row, dict) or row.get("direction") != "received" or
                        not isinstance(message, dict) or
                        message.get("method") != "thread/tokenUsage/updated"):
                    continue
                params = message.get("params")
                if (isinstance(params, dict) and
                        params.get("threadId") == self.handle.thread_id and
                        params.get("turnId") == self.handle.turn_id):
                    match = (line, params.get("tokenUsage"))
                    break
            if match is None:
                raise RuntimeError("new usage notification has no retained raw row")
            source_bytes, source_usage = match
            if source_usage != token_usage:
                raise RuntimeError("usage notification differs from retained raw row")
            usage = _normalized_late_usage(token_usage)
            usage_bytes = json.dumps(
                usage, allow_nan=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8")
            self._cursor = (next_count, offset + consumed_bytes)
            return {"usage": usage, "usage_bytes": usage_bytes,
                    "source_bytes": source_bytes,
                    "observed_ns": time.perf_counter_ns()}


class _LateSpoolUsageSource:
    """Read hash-bound, same-turn usage sidecars from the host spool worker."""

    def __init__(self, planner, handle, journal_path):
        self.planner = planner
        self.handle = handle
        self.journal_path = Path(journal_path)
        self._sequence = 1
        self._captured = False
        self._lock = threading.Lock()

    def capture_terminal(self):
        """Mark caller custody without blocking for the host receipt to land."""
        with self._lock:
            self._captured = True

    def read(self, timeout):
        """Return one usage sidecar; never inspect a terminal answer payload."""
        if (type(timeout) not in (int, float) or not 0 <= timeout <= 30):
            raise ValueError("late spool usage wait must be between 0 and 30 seconds")
        with self._lock:
            if not self._captured:
                raise RuntimeError("late spool usage requires terminal custody")
            payload = self.planner.wait_late_usage_sidecar(
                self.handle, self._sequence, timeout)
            if payload is None:
                return None
            terminal_cursor = payload.get("terminal_cursor")
            record = payload.get("record")
            if (type(terminal_cursor) is not tuple or len(terminal_cursor) != 2 or
                    any(type(value) is not int or value < 0 for value in terminal_cursor) or
                    not isinstance(record, dict)):
                raise ValueError("late spool usage source returned a malformed record")
            usage_raw = record["usage"]
            source_bytes = record["source_jsonl"].encode("utf-8")
            offset = record["journal_offset"]
            if offset < terminal_cursor[1] or self.journal_path.stat().st_size < offset:
                raise RuntimeError("late spool usage is outside its timeout journal boundary")
            matched = None
            with self.journal_path.open("rb") as stream:
                stream.seek(offset)
                for line in stream:
                    try:
                        row = json.loads(line)
                    except (TypeError, ValueError):
                        continue
                    message = row.get("message") if isinstance(row, dict) else None
                    params = message.get("params") if isinstance(message, dict) else None
                    if (isinstance(row, dict) and row.get("direction") == "received" and
                            isinstance(message, dict) and
                            message.get("method") == "thread/tokenUsage/updated" and
                            isinstance(params, dict) and
                            params.get("threadId") == self.handle.thread_id and
                            params.get("turnId") == self.handle.turn_id):
                        matched = (line, params.get("tokenUsage"))
                        break
            if matched != (source_bytes, usage_raw):
                raise RuntimeError("late spool sidecar differs from the retained protocol row")
            usage = _normalized_late_usage(usage_raw)
            usage_bytes = json.dumps(
                usage, allow_nan=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8")
            self._sequence += 1
            return {"usage": usage, "usage_bytes": usage_bytes,
                    "source_bytes": source_bytes,
                    "observed_ns": time.perf_counter_ns()}


def parse_app_server_tool_request(response_bytes, *, thread_id, turn_id):
    """Read the one completed structured answer from a retained protocol slice."""
    if not isinstance(response_bytes, bytes):
        raise TypeError("app-server response must be raw protocol journal bytes")
    completions = []
    for line in response_bytes.splitlines():
        if not line:
            continue
        row = json.loads(line)
        message = row.get("message") if isinstance(row, dict) else None
        if (row.get("direction") != "received" or not isinstance(message, dict) or
                message.get("method") != "turn/completed"):
            continue
        params = message.get("params", {})
        turn = params.get("turn", {}) if isinstance(params, dict) else {}
        if params.get("threadId") == thread_id and turn.get("id") == turn_id:
            completions.append(turn)
    if len(completions) != 1:
        raise ValueError("exactly one matching app-server turn completion is required")
    turn = completions[0]
    if turn.get("status") != "completed":
        raise ValueError("app-server turn did not complete")
    messages = [item for item in turn.get("items", [])
                if isinstance(item, dict) and item.get("type") == "agentMessage"]
    if len(messages) != 1 or not isinstance(messages[0].get("text"), str):
        raise ValueError("exactly one completed app-server agent message is required")
    result = json.loads(messages[0]["text"])
    if not isinstance(result, dict):
        raise ValueError("app-server tool request must be a JSON object")
    return result


class AppServerPublicMcpModelCall:
    """Expose a persistent planner turn through the existing model-call contract.

    ``planner`` is a ``PersistentPlannerAdapter`` with an already-started
    session. ``protocol_journal_path`` is the exact journal used by its
    ``CodexAppServerClient``. The caller owns and closes both objects.
    """

    def __init__(self, planner, protocol_journal_path, *, workspace, contract,
                 output_schema, model, effort, path_converter=str,
                 turn_timeout=90):
        if not callable(getattr(planner, "begin_turn", None)) or not callable(
                getattr(planner, "await_turn", None)):
            raise TypeError("planner must expose begin_turn and await_turn")
        if not isinstance(output_schema, dict):
            raise TypeError("output_schema must be an object")
        if type(turn_timeout) is not int or turn_timeout <= 0:
            raise ValueError("turn_timeout must be a positive integer")
        self.planner = planner
        self.protocol_journal_path = Path(protocol_journal_path).resolve()
        self.workspace = Path(workspace).resolve()
        self.contract = contract
        self.output_schema = output_schema
        self.model = model
        self.effort = effort
        self.path_converter = path_converter
        self.turn_timeout = turn_timeout
        self._lock = threading.Lock()

    def call(self, root, prompt, image, contract, workspace):
        """Run exactly one structured turn and retain its raw protocol slice."""
        if contract != self.contract:
            raise ValueError("call contract differs from app-server session contract")
        if Path(workspace).resolve() != self.workspace:
            raise ValueError("workspace differs from app-server session workspace")
        root = Path(root)
        root.mkdir(parents=True, exist_ok=False)
        image = Path(image).resolve(strict=True)
        events_path = root / "model" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=False)
        (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")

        handle = None
        turn = None
        protocol_bytes = b""
        before = None
        call_error = None
        started_ns = time.perf_counter_ns()
        try:
            with self._lock:
                # A file-spool planner may cause the host App Server to create
                # the shared journal only after it atomically claims the
                # request. Treat that first turn as an offset-zero slice.
                before = (self.protocol_journal_path.stat().st_size
                          if self.protocol_journal_path.exists() else 0)
                handle = self.planner.begin_turn(
                    prompt, output_schema=self.output_schema,
                    image_path=self.path_converter(image))
                try:
                    turn = self.planner.await_turn(handle, timeout=self.turn_timeout)
                except BaseException as exc:
                    call_error = exc
                journal = self.protocol_journal_path.read_bytes()
                if len(journal) < before:
                    raise RuntimeError("app-server protocol journal was truncated")
                protocol_bytes = journal[before:]
        finally:
            # Keep partial send/receive evidence even when the planner raises.
            if not protocol_bytes and self.protocol_journal_path.exists():
                try:
                    current = self.protocol_journal_path.read_bytes()
                    if before is not None and len(current) >= before:
                        protocol_bytes = current[before:]
                except OSError:
                    pass
            events_path.write_bytes(protocol_bytes)

        if call_error is not None:
            if handle is not None:
                partial_usage = _best_effort_partial_turn_usage(
                    protocol_bytes, thread_id=handle.thread_id,
                    turn_id=handle.turn_id)
                if partial_usage is not None:
                    reported_usage = _partial_turn_usage(
                        getattr(call_error, "usage", None))
                    if reported_usage is None or reported_usage == partial_usage:
                        call_error.usage = {"status": "partial", **partial_usage}
                    else:
                        call_error.usage = None
                        call_error.usage_error = (
                            "exception usage differs from retained protocol journal")
                if isinstance(call_error, TimeoutError):
                    spool_source = getattr(self.planner, "late_usage_source", None)
                    if callable(spool_source):
                        call_error.late_usage_source = spool_source(
                            handle, self.protocol_journal_path)
                    elif (callable(getattr(self.planner, "late_usage_cursor", None)) and
                            callable(getattr(self.planner, "wait_late_usage", None))):
                        call_error.late_usage_source = _LateAppServerUsageSource(
                            self.planner, handle, self.protocol_journal_path)
            raise call_error

        if turn is None or not getattr(turn, "answer_eligible", False):
            error = RuntimeError("app-server answer is ineligible; no tool call")
            error.call_id = getattr(handle, "turn_id", None)
            error.thread_id = getattr(handle, "thread_id", None)
            if handle is not None:
                journal_usage = _partial_turn_usage(_journal_turn_usage(
                    protocol_bytes, thread_id=handle.thread_id,
                    turn_id=handle.turn_id))
                if turn is None:
                    # No terminal turn object exists to cross-check the
                    # nonterminal usage update. Preserve it as partial usage;
                    # the recorder must not report a known count as missing.
                    error.usage = journal_usage
                else:
                    usage = _partial_turn_usage(getattr(turn, "usage", None))
                    if usage == journal_usage:
                        error.usage = usage
                    else:
                        error.usage = None
                        error.usage_error = (
                            "ineligible turn usage differs from retained protocol journal")
            else:
                error.usage = None
            raise error

        usage = _turn_usage(getattr(turn, "usage", None))
        journal_usage = _turn_usage(_journal_turn_usage(
            protocol_bytes, thread_id=handle.thread_id, turn_id=handle.turn_id))
        if usage != journal_usage:
            raise ValueError(
                "app-server turn usage differs from its retained protocol journal")
        result = {
            "raw": turn.answer,
            "usage": usage,
            "call_id": handle.turn_id,
            "thread_id": handle.thread_id,
            "turn_id": handle.turn_id,
            "turn_status": turn.status,
            "answer_eligible": True,
            "runner_ns": time.perf_counter_ns() - started_ns,
            "requested_model": self.model,
            "requested_effort": self.effort,
            "cost": None,
        }
        (root / "result.json").write_text(
            json.dumps(result, allow_nan=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        return result
