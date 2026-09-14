"""Persistent app-server implementation of the integrated grounding call contract."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

try:
    from .codex_app_server_client_v2 import CodexAppServerClient
    from .codex_app_server_command_v1 import command as app_server_command
    from .compiled_form_grounding_v1 import validate as validate_compiled
    from .plain_form_points_v1 import validate as validate_plain
    from .persistent_planner_adapter_v2 import PersistentPlannerAdapter
except ImportError:  # Script-oriented research callers add this directory to sys.path.
    from codex_app_server_client_v2 import CodexAppServerClient
    from codex_app_server_command_v1 import command as app_server_command
    from compiled_form_grounding_v1 import validate as validate_compiled
    from plain_form_points_v1 import validate as validate_plain
    from persistent_planner_adapter_v2 import PersistentPlannerAdapter


HERE = Path(__file__).resolve().parent
CONTRACTS = {
    "plain": (HERE / "plain_form_points_schema_v1.json",
              HERE / "plain_form_points_responder_v1.txt", validate_plain),
    "compiled": (HERE / "compiled_form_grounding_schema_v1.json",
                 HERE / "compiled_form_grounding_responder_v1.txt", validate_compiled),
}


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


USAGE_MAP = {
    "inputTokens": "input_tokens",
    "cachedInputTokens": "cached_input_tokens",
    "cacheWriteInputTokens": "cache_write_input_tokens",
    "outputTokens": "output_tokens",
    "reasoningOutputTokens": "reasoning_output_tokens",
}


def per_turn_usage(value):
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


class PersistentGroundingModel:
    """Keep one typed model thread across cold grounding and later repair."""

    def __init__(self, session_root, workspace, *, node, cli,
                 contract="compiled", model="gpt-5.6-luna", effort="low",
                 client=None, path_converter=windows_path):
        if contract not in CONTRACTS:
            raise ValueError("contract must be plain or compiled")
        self.session_root = Path(session_root)
        self.workspace = Path(workspace).resolve()
        self.contract = contract
        self.model = model
        self.effort = effort
        self.path_converter = path_converter
        self.session_root.mkdir(parents=True, exist_ok=False)
        self._owns_client = client is None
        self.client = client or CodexAppServerClient(
            app_server_command(node, cli), cwd=self.workspace,
            journal_path=self.session_root / "protocol.jsonl")
        if self._owns_client:
            self.client.initialize()
        _schema, instructions, _validator = CONTRACTS[contract]
        self.planner = PersistentPlannerAdapter(
            self.client, model=model, effort=effort,
            cwd=self.path_converter(self.workspace),
            base_instructions=Path(instructions).read_text(encoding="utf-8"))
        self.thread_id = self.planner.start_session()
        self.calls = 0

    def call(self, root: Path, prompt: str, image: Path, contract: str, workspace: Path):
        if contract != self.contract:
            raise ValueError("call contract differs from persistent session contract")
        if Path(workspace).resolve() != self.workspace:
            raise ValueError("workspace differs from persistent session workspace")
        root = Path(root)
        root.mkdir(parents=True, exist_ok=False)
        (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
        schema_path, _instructions, validator = CONTRACTS[contract]
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        started = time.perf_counter_ns()
        handle = self.planner.begin_turn(
            prompt, output_schema=schema,
            image_path=self.path_converter(Path(image).resolve()))
        turn = self.planner.await_turn(handle, timeout=90)
        elapsed = time.perf_counter_ns() - started
        self.calls += 1
        if not turn.answer_eligible:
            failure = {
                "thread_id": handle.thread_id, "turn_id": handle.turn_id,
                "status": turn.status, "answer_eligible": False,
                "error": turn.error, "usage": per_turn_usage(turn.usage),
                "runner_ns": elapsed,
            }
            (root / "failure.json").write_text(
                json.dumps(failure, indent=2) + "\n", encoding="utf-8", newline="\n")
            raise RuntimeError("persistent grounding answer ineligible; no retry")
        raw = turn.answer
        normalized = validator(raw)
        result = {
            "raw": raw,
            "grounding": normalized,
            "usage": per_turn_usage(turn.usage),
            "call_id": handle.turn_id,
            "thread_id": handle.thread_id,
            "turn_id": handle.turn_id,
            "turn_status": turn.status,
            "answer_eligible": True,
            "runner_ns": elapsed,
            "requested_model": self.model,
            "requested_effort": self.effort,
            "cost": None,
        }
        (root / "result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        return result

    def close(self):
        if self._owns_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
