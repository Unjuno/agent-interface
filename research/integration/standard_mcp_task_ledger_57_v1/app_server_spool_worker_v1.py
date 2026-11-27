"""Host-side one-request Codex App Server worker for the file spool."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import tomllib
import time

from app_server_file_spool_v1 import claim_next, publish_late_usage, publish_stage
from codex_app_server_client_v1 import CodexAppServerClient
from persistent_planner_adapter_v1 import PersistentPlannerAdapter


_BASE_INSTRUCTIONS = (
    "Return one JSON object matching the supplied output schema. Use only the "
    "provided prompt and image. Do not call tools, read files, or request approval."
)
_LATE_USAGE_GRACE_SECONDS = 5.0


def _assert_no_mcp_tools(client, thread_id: str) -> None:
    """Fail closed unless every configured server is explicitly disabled."""
    cursor = None
    pages = 0
    active = 0
    while True:
        params = {"threadId": thread_id, "detail": "toolsAndAuthOnly", "limit": 100}
        if cursor is not None:
            params["cursor"] = cursor
        page = client.request("mcpServerStatus/list", params)
        rows = page.get("data")
        if not isinstance(rows, list):
            raise RuntimeError("MCP status response omitted its server list")
        for server in rows:
            if not isinstance(server, dict) or server.get("runtimeStatus") != "disabled":
                active += 1
                continue
            tools = server.get("tools")
            # App Server versions have represented the empty tool collection
            # as either [] or {}. Accept only these explicit empty containers;
            # missing or unknown shapes remain fail-closed.
            if not isinstance(tools, (list, dict)) or tools:
                active += 1
        pages += 1
        if pages > 20:
            raise RuntimeError("MCP status pagination exceeded the worker bound")
        cursor = page.get("nextCursor")
        if cursor is None:
            break
        if not isinstance(cursor, str) or not cursor:
            raise RuntimeError("MCP status returned an invalid pagination cursor")
    if active:
        raise RuntimeError(f"refusing model turn: {active} MCP servers are not disabled")


def _harvest_late_usage(root: Path, attempt_id: str, planner, handle,
                        protocol_path: Path, cursor: tuple[int, int], *,
                        grace_seconds: float) -> list[dict]:
    """Persist only fresh same-turn usage notifications within a fixed bound."""
    if (type(cursor) is not tuple or len(cursor) != 2 or
            any(type(value) is not int or value < 0 for value in cursor)):
        raise ValueError("late usage cursor is invalid")
    deadline = time.monotonic() + grace_seconds
    count, offset = cursor
    receipts = []
    while time.monotonic() < deadline:
        received = planner.wait_late_usage(
            handle, (count, offset), max(0.0, deadline - time.monotonic()))
        if received is None:
            break
        token_usage, next_count = received
        if type(next_count) is not int or next_count != count + 1:
            raise RuntimeError("late usage cursor did not advance by one")
        if not isinstance(token_usage, dict):
            raise RuntimeError("late usage notification omitted tokenUsage")
        if protocol_path.stat().st_size < offset:
            raise RuntimeError("App Server journal was truncated during late usage wait")
        with protocol_path.open("rb") as stream:
            stream.seek(offset)
            appended = stream.read()
        matched = None
        consumed = 0
        for line in appended.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                break
            consumed += len(line)
            try:
                row = json.loads(line)
            except (UnicodeError, json.JSONDecodeError):
                continue
            message = row.get("message") if isinstance(row, dict) else None
            params = message.get("params") if isinstance(message, dict) else None
            if (isinstance(row, dict) and row.get("direction") == "received" and
                    isinstance(message, dict) and
                    message.get("method") == "thread/tokenUsage/updated" and
                    isinstance(params, dict) and
                    params.get("threadId") == handle.thread_id and
                    params.get("turnId") == handle.turn_id):
                matched = (line, params.get("tokenUsage"))
                break
        if matched is None:
            raise RuntimeError("new same-turn usage notification has no retained JSONL row")
        source_line, source_usage = matched
        if source_usage != token_usage:
            raise RuntimeError("late usage differs from its retained App Server row")
        source_hash = hashlib.sha256(source_line).hexdigest()
        journal_hash = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
        record = {
            "thread_id": handle.thread_id,
            "turn_id": handle.turn_id,
            "journal_offset": offset,
            "usage": token_usage,
            "source_jsonl": source_line.decode("utf-8"),
            "source_jsonl_sha256": source_hash,
            "protocol_journal_sha256_at_observation": journal_hash,
        }
        sequence = len(receipts) + 1
        publish_late_usage(root, attempt_id, sequence, record)
        receipts.append({"sequence": sequence, "usage": token_usage,
                         "source_jsonl_sha256": source_hash})
        count, offset = next_count, offset + consumed
    return receipts


def process_one_request(root: Path, *, command: list[str], cwd: str | Path,
                        model: str, effort: str, expected_schema_sha256: str,
                        turn_timeout: int = 90) -> dict:
    """Claim at most one request, run one bounded turn, and never retry it."""
    if type(turn_timeout) is not int or not 1 <= turn_timeout <= 300:
        raise ValueError("turn_timeout must be between 1 and 300 seconds")
    root = Path(root).resolve()
    request = claim_next(root, expected_model=model, expected_effort=effort,
        expected_schema_sha256=expected_schema_sha256)
    if request is None:
        return {"status": "idle"}

    protocol_path = root / "protocol.jsonl"
    if protocol_path.exists():
        publish_stage(root, request["attempt_id"], "unknown", {
            "error": "protocol journal already exists; worker refuses to reuse it"})
        raise RuntimeError("spool protocol journal already exists")

    client = None
    planner = None
    handle = None
    result = None
    error = None
    late_usage_cursor = None
    awaiting_turn = False
    started_ns = time.perf_counter_ns()
    try:
        client = CodexAppServerClient(command, cwd=cwd, journal_path=str(protocol_path))
        client.initialize()
        planner = PersistentPlannerAdapter(
            client,
            model=model,
            effort=effort,
            cwd=str(Path(cwd).resolve()),
            base_instructions=_BASE_INSTRUCTIONS,
            thread_config={
                "project_doc_max_bytes": 0,
                "mcp_servers": {
                    "node_repl": {"enabled": False},
                    "openaiDeveloperDocs": {"enabled": False},
                },
            },
        )
        planner.start_session()
        _assert_no_mcp_tools(client, planner.thread_id)
        handle = planner.begin_turn(
            request["prompt"],
            output_schema=request["output_schema"],
            image_path=request["_image_path"],
        )
        publish_stage(root, request["attempt_id"], "started", {
            "thread_id": handle.thread_id,
            "turn_id": handle.turn_id,
            "model": model,
            "effort": effort,
        })
        awaiting_turn = True
        result = planner.await_turn(handle, timeout=turn_timeout)
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        if isinstance(exc, TimeoutError) and awaiting_turn and planner is not None and handle is not None:
            try:
                late_usage_cursor = planner.late_usage_cursor(handle)
            except BaseException as cursor_error:
                error["late_usage_cursor_error"] = {
                    "type": type(cursor_error).__name__,
                    "message": str(cursor_error),
                }
        if late_usage_cursor is None and planner is not None and handle is not None:
            try:
                planner.interrupt(handle)
            except BaseException as interrupt_error:
                error["interrupt_error"] = {
                    "type": type(interrupt_error).__name__,
                    "message": str(interrupt_error),
                }
    finally:
        if client is not None and late_usage_cursor is None:
            try:
                client.close(timeout=10)
            except BaseException as close_error:
                error = error or {"type": "ClientCloseError", "message": "App Server cleanup failed"}
                error["close_error"] = {
                    "type": type(close_error).__name__,
                    "message": str(close_error),
                }

    # The App Server journal is the authoritative custody record for setup
    # failures too (including a turn that was never sent). Keep it beside the
    # terminal receipt so UNKNOWN can be diagnosed without guessing.
    try:
        protocol_sha256 = None
        if protocol_path.is_file():
            import hashlib
            protocol_sha256 = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    except OSError as journal_error:
        protocol_sha256 = None
        error = error or {"type": "ProtocolJournalError", "message": "protocol journal could not be read"}
        error["journal_error"] = type(journal_error).__name__

    elapsed_ns = time.perf_counter_ns() - started_ns
    if error is not None or result is None or handle is None:
        record = {
            "thread_id": None if handle is None else handle.thread_id,
            "turn_id": None if handle is None else handle.turn_id,
            "status": "unknown",
            "answer_eligible": False,
            "answer": None,
            "usage": None,
            "error": error or {"type": "Unknown", "message": "turn did not produce a terminal result"},
            "cancellation_requested": False,
            "completed_agent_messages": 0,
            "worker_elapsed_ns": elapsed_ns,
            "protocol_journal_sha256": protocol_sha256,
        }
        if late_usage_cursor is not None:
            record["late_usage_grace_seconds"] = _LATE_USAGE_GRACE_SECONDS
            record["late_usage_cursor"] = list(late_usage_cursor)
        try:
            publish_stage(root, request["attempt_id"], "unknown", record)
            if late_usage_cursor is not None and handle is not None:
                try:
                    record["late_usage_receipts"] = _harvest_late_usage(
                        root, request["attempt_id"], planner, handle, protocol_path,
                        late_usage_cursor, grace_seconds=_LATE_USAGE_GRACE_SECONDS)
                except BaseException as harvest_error:
                    record["late_usage_harvest_error"] = {
                        "type": type(harvest_error).__name__,
                        "message": str(harvest_error),
                    }
        finally:
            if client is not None and late_usage_cursor is not None:
                try:
                    client.close(timeout=10)
                except BaseException as close_error:
                    record["close_error"] = {
                        "type": type(close_error).__name__,
                        "message": str(close_error),
                    }
        return record

    record = {
        "thread_id": handle.thread_id,
        "turn_id": handle.turn_id,
        "status": result.status,
        "answer_eligible": result.answer_eligible,
        "answer": result.answer,
        "usage": result.usage,
        "error": result.error,
        "cancellation_requested": result.cancellation_requested,
        "completed_agent_messages": result.completed_agent_messages,
        "worker_elapsed_ns": elapsed_ns,
        "protocol_journal_sha256": protocol_sha256,
    }
    publish_stage(root, request["attempt_id"], "completed", record)
    return record


def _configured_mcp_server_names(codex_home: str | Path | None = None) -> tuple[str, ...]:
    """Return configured MCP names only; never read or expose their values."""
    if codex_home is None:
        configured_home = os.environ.get("CODEX_HOME")
        codex_home = configured_home if configured_home else Path.home() / ".codex"
    config_path = Path(codex_home) / "config.toml"
    if not config_path.is_file():
        return ()
    with config_path.open("rb") as stream:
        config = tomllib.load(stream)
    servers = config.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcp_servers must be a table in Codex config")
    names = tuple(sorted(servers))
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("Codex MCP server names must be nonempty strings")
    return names


def _mcp_override_key(name: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return name
    return json.dumps(name, ensure_ascii=False)


def command(cli_path: str | Path, *, codex_home: str | Path | None = None) -> list[str]:
    """Start a planner-only server with feature families and configured MCPs disabled."""
    args = [str(cli_path), "app-server", "--stdio"]
    for feature in (
        "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
        "in_app_browser", "code_mode", "code_mode_host", "computer_use",
        "enable_mcp_apps", "mcp_2026_07_28", "codex_apps_mcp_2026_07_28",
        "unified_exec", "unified_exec_tty", "view_image", "standalone_web_search",
        "web_search_cached", "web_search_request", "browser_use_full_cdp_access",
    ):
        args.extend(("--disable", feature))
    # An App Server thread's mcp_servers override does not clear configured
    # servers. Disable only names that exist: adding unknown partial tables can
    # make newer CLI versions reject startup as an invalid transport.
    for name in _configured_mcp_server_names(codex_home):
        args.extend(("-c", f"mcp_servers.{_mcp_override_key(name)}.enabled=false"))
    return args
