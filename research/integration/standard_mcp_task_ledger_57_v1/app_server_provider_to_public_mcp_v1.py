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
        started_ns = time.perf_counter_ns()
        try:
            with self._lock:
                before = self.protocol_journal_path.stat().st_size
                handle = self.planner.begin_turn(
                    prompt, output_schema=self.output_schema,
                    image_path=self.path_converter(image))
                turn = self.planner.await_turn(handle, timeout=self.turn_timeout)
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

        if turn is None or not getattr(turn, "answer_eligible", False):
            error = RuntimeError("app-server answer is ineligible; no tool call")
            error.call_id = getattr(handle, "turn_id", None)
            error.thread_id = getattr(handle, "thread_id", None)
            error.usage = getattr(turn, "usage", None)
            raise error

        usage = _turn_usage(getattr(turn, "usage", None))
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
