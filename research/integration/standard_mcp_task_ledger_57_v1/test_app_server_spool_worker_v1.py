from pathlib import Path
import hashlib
import json
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import os

from app_server_file_spool_v1 import (
    _canonical_json_sha256,
    claim_next,
    publish_late_usage,
    publish_request,
    wait_for_stage,
)
import app_server_spool_worker_v1 as worker


class FakeClient:
    def __init__(self, command, *, cwd, journal_path):
        self.journal_path = Path(journal_path)
        self.journal_path.open("x", encoding="utf-8").close()
        self.closed = False

    def initialize(self):
        return {"userAgent": "fake"}

    def request(self, method, params=None, timeout=30):
        if method != "mcpServerStatus/list":
            raise AssertionError(method)
        return {"data": [{"name": "fake-disabled", "runtimeStatus": "disabled",
            "tools": {}}], "nextCursor": None}

    def close(self, timeout=5):
        self.closed = True


class FakePlanner:
    begin_calls = 0

    def __init__(self, client, **kwargs):
        self.client = client
        self.handle = None
        self.thread_id = None

    def start_session(self):
        self.thread_id = "thread-1"
        return "thread-1"

    def begin_turn(self, prompt, *, output_schema, image_path):
        type(self).begin_calls += 1
        self.handle = SimpleNamespace(thread_id="thread-1", turn_id="turn-1")
        return self.handle

    def await_turn(self, handle, timeout):
        return SimpleNamespace(status="completed", answer_eligible=True,
            answer={"tool": "interface_guarded_calc_compiled"}, error=None,
            usage={"last": {"inputTokens": 21, "outputTokens": 8}},
            cancellation_requested=False, completed_agent_messages=1)

    def interrupt(self, handle):
        return {"outcome": "requested"}


class FailingPlanner(FakePlanner):
    def await_turn(self, handle, timeout):
        raise TimeoutError("synthetic provider wait timeout")


class LateUsagePlanner(FailingPlanner):
    last_instance = None

    def __init__(self, client, **kwargs):
        super().__init__(client, **kwargs)
        type(self).last_instance = self
        self.waits = 0
        self.interrupted = False

    def late_usage_cursor(self, handle):
        return 0, self.client.journal_path.stat().st_size

    def wait_late_usage(self, handle, cursor, timeout):
        self.waits += 1
        if not 0 <= timeout <= worker._LATE_USAGE_GRACE_SECONDS:
            raise AssertionError("late usage wait exceeded the fixed grace")
        unknown_path = self.client.journal_path.parent / "responses" / "attempt-1.unknown.json"
        if not unknown_path.is_file():
            raise AssertionError("UNKNOWN must be durable before late usage is read")
        if self.interrupted:
            raise AssertionError("timed out App Server turn must not be interrupted")
        if self.waits > 2:
            return None
        rows = []
        if self.waits == 1:
            rows.append({"direction": "received", "observed_ns": 1, "message": {
                "method": "turn/completed", "params": {"threadId": handle.thread_id,
                    "turn": {"id": handle.turn_id, "status": "completed",
                        "items": [{"type": "agentMessage", "text": '{"tool":"unsafe"}'}]}}}})
        usage = {"last": {"inputTokens": 34 if self.waits == 1 else 40,
                           "outputTokens": 13 if self.waits == 1 else 15}}
        rows.append({"direction": "received", "observed_ns": self.waits + 1, "message": {
                "method": "thread/tokenUsage/updated", "params": {
                    "threadId": handle.thread_id, "turnId": handle.turn_id,
                    "tokenUsage": usage}}})
        with self.client.journal_path.open("ab") as stream:
            for row in rows:
                stream.write(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
        return usage, self.waits

    def interrupt(self, handle):
        self.interrupted = True
        return super().interrupt(handle)


class ActiveMcpClient(FakeClient):
    def request(self, method, params=None, timeout=30):
        return {"data": [{"name": "fake-active", "runtimeStatus": "connected",
            "tools": {"external-action": {}}}], "nextCursor": None}


class AppServerSpoolWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / "attempts" / "attempt-1" / "frame.png"
        self.image.parent.mkdir(parents=True)
        self.image.write_bytes(b"PNG test fixture")
        self.schema = {"type": "object", "required": ["tool"]}
        self.schema_hash = _canonical_json_sha256(self.schema)
        publish_request(self.root, attempt_id="attempt-1", prompt="Choose a tool.",
            output_schema=self.schema, image_path=self.image,
            model="gpt-6.1-sol", effort="medium")

    def tearDown(self):
        self.temp.cleanup()

    def test_command_disables_only_mcp_servers_present_in_codex_config(self):
        home = self.root / "codex-home"
        home.mkdir()
        (home / "config.toml").write_text(
            '[mcp_servers.node_repl]\ncommand = "node"\n'
            '[mcp_servers."private.mcp"]\ncommand = "node"\n',
            encoding="utf-8")
        result = worker.command("codex.exe", codex_home=home)
        overrides = [result[index + 1] for index, value in enumerate(result[:-1])
                     if value == "-c" and result[index + 1].startswith("mcp_servers.")]
        self.assertEqual(overrides, [
            "mcp_servers.node_repl.enabled=false",
            'mcp_servers."private.mcp".enabled=false',
        ])
        self.assertNotIn("mcp_servers.cua_repl.enabled=false", result)

    def test_command_uses_codex_home_environment_and_does_not_add_absent_names(self):
        home = self.root / "codex-home-env"
        home.mkdir()
        (home / "config.toml").write_text(
            '[mcp_servers.openaiDeveloperDocs]\nurl = "https://example.invalid"\n',
            encoding="utf-8")
        with patch.dict(os.environ, {"CODEX_HOME": str(home)}):
            result = worker.command("codex.exe")
        overrides = [value for value in result if value.startswith("mcp_servers.")]
        self.assertEqual(overrides, ["mcp_servers.openaiDeveloperDocs.enabled=false"])
        self.assertNotIn("mcp_servers.blender.enabled=false", result)

    def run_worker(self, planner_type, client_type=FakeClient):
        with patch.object(worker, "CodexAppServerClient", client_type), \
                patch.object(worker, "PersistentPlannerAdapter", planner_type):
            return worker.process_one_request(self.root, command=["fake-codex"],
                cwd=self.root, model="gpt-6.1-sol", effort="medium",
                expected_schema_sha256=self.schema_hash, turn_timeout=1)

    def test_worker_publishes_joinable_terminal_usage_and_closes_client(self):
        result = self.run_worker(FakePlanner)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["answer_eligible"])
        self.assertEqual(result["usage"]["last"]["inputTokens"], 21)
        self.assertEqual(result["thread_id"], "thread-1")
        self.assertEqual(result["turn_id"], "turn-1")
        self.assertEqual(wait_for_stage(self.root, "attempt-1", "started", timeout=0.1)["turn_id"], "turn-1")
        self.assertEqual(wait_for_stage(self.root, "attempt-1", "completed", timeout=0.1)["usage"], result["usage"])
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_hash))

    def test_worker_timeout_is_unknown_and_never_requeues(self):
        result = self.run_worker(FailingPlanner)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["answer_eligible"])
        self.assertEqual(result["error"]["type"], "TimeoutError")
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_hash))
        self.assertEqual(wait_for_stage(self.root, "attempt-1", "unknown", timeout=0.1)["status"], "unknown")

    def test_worker_publishes_unknown_then_captures_late_usage_without_reading_answer(self):
        result = self.run_worker(LateUsagePlanner)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["answer_eligible"])
        self.assertIsNone(result["answer"])
        self.assertEqual([item["usage"]["last"]["inputTokens"]
                          for item in result["late_usage_receipts"]], [34, 40])
        self.assertEqual(result["late_usage_grace_seconds"], worker._LATE_USAGE_GRACE_SECONDS)
        self.assertFalse(LateUsagePlanner.last_instance.interrupted)
        self.assertTrue(LateUsagePlanner.last_instance.client.closed)
        receipt = wait_for_stage(self.root, "attempt-1", "unknown", timeout=0.1)
        self.assertEqual(receipt["status"], "unknown")
        for sequence, expected_tokens in ((1, 34), (2, 40)):
            sidecar = self.root / "responses" / f"attempt-1.late-usage-{sequence:06d}.json"
            source = sidecar.read_text(encoding="utf-8")
            saved = json.loads(source)
            self.assertEqual(saved["schema"], "agent-interface/app-server-spool-late-usage-v1")
            self.assertEqual(saved["sequence"], sequence)
            self.assertEqual(saved["record"]["thread_id"], "thread-1")
            self.assertEqual(saved["record"]["turn_id"], "turn-1")
            self.assertEqual(saved["record"]["usage"]["last"]["inputTokens"], expected_tokens)
            self.assertIn('"method":"thread/tokenUsage/updated"', saved["record"]["source_jsonl"])
            self.assertEqual(saved["record"]["source_jsonl_sha256"], hashlib.sha256(
                saved["record"]["source_jsonl"].encode("utf-8")).hexdigest())
            self.assertNotIn("unsafe", source)
            with self.assertRaises(FileExistsError):
                publish_late_usage(self.root, "attempt-1", sequence,
                    {"usage": {"last": {"inputTokens": 0}}})
        self.assertNotIn("late_usage_receipts", receipt)
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_hash))

    def test_worker_refuses_generation_when_any_mcp_tool_is_visible(self):
        FakePlanner.begin_calls = 0
        result = self.run_worker(FakePlanner, ActiveMcpClient)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["answer_eligible"])
        self.assertIn("refusing model turn", result["error"]["message"])
        self.assertEqual(FakePlanner.begin_calls, 0)


if __name__ == "__main__":
    unittest.main()
