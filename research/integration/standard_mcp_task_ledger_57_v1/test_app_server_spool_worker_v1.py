from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from app_server_file_spool_v1 import (
    _canonical_json_sha256,
    claim_next,
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

    def test_worker_refuses_generation_when_any_mcp_tool_is_visible(self):
        FakePlanner.begin_calls = 0
        result = self.run_worker(FakePlanner, ActiveMcpClient)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["answer_eligible"])
        self.assertIn("refusing model turn", result["error"]["message"])
        self.assertEqual(FakePlanner.begin_calls, 0)


if __name__ == "__main__":
    unittest.main()
