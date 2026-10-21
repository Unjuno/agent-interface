"""Compose the real JSONL client with grounding and the adaptive attempt ledger."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from research.live_control import adaptive_acquisition_caller_v3 as caller
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.integrated_efficiency_app_server_model_v1 import (
    PersistentGroundingModel,
)


PEER = r'''
import json, sys

def send(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if method == "initialized":
        continue
    if method == "initialize":
        send({"id": request["id"], "result": {}})
    elif method == "thread/start":
        send({"id": request["id"], "result": {"thread": {"id": "thread-ledger-1"}}})
    elif method == "turn/start":
        send({"id": request["id"], "result": {"turn": {"id": "turn-ledger-1"}}})
        send({"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-ledger-1", "turnId": "turn-ledger-1",
            "tokenUsage": {"last": {"inputTokens": 1234,
                "cachedInputTokens": 234, "cacheWriteInputTokens": 0,
                "outputTokens": 56, "reasoningOutputTokens": 12}}}})
        send({"method": "turn/completed", "params": {
            "threadId": "thread-ledger-1", "turn": {
                "id": "turn-ledger-1", "status": "completed",
                "items": [{"type": "agentMessage", "text": "{}"}]}}})
    else:
        send({"id": request.get("id"), "error": {"code": -32000,
            "message": "unexpected fixture method: " + str(method)}})
'''


class GroundingAppServerUsageTransportTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "app-server pipe transport requires Windows Python 3.12+")
    def test_thread_and_turn_identity_with_usage_reach_failed_attempt_ledger(self):
        with tempfile.TemporaryDirectory(prefix="grounding-appserver-ledger-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic app-server composition fixture")
            journal_path = root / "protocol.jsonl"
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", PEER],
                cwd=str(workspace), journal_path=str(journal_path))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str)
                events = []
                execute_calls = []

                def anchor(_payload):
                    value = model.call(root / "call", "synthetic request", image,
                                       "compiled", workspace)
                    return {"call_id": value["call_id"],
                            "output": {"status": "target_reference",
                                       "target": value["grounding"]},
                            "usage": value["usage"],
                            "requested_model": value["requested_model"],
                            "requested_effort": value["requested_effort"],
                            "cost": value["cost"],
                            "visible_images_submitted": 1,
                            "wait_ns": value["runner_ns"]}

                result = caller.run({
                    "target": "synthetic form", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [], "repair_on": [],
                    "session_id": "synthetic-appserver-session"},
                    {"observe_source": lambda _payload: {},
                     "acquire_anchor": lambda _payload: {},
                     "anchor_model": anchor,
                     "final_revalidate": lambda _payload: {"status": "revalidated"},
                     "execute": lambda payload: execute_calls.append(payload) or
                         {"status": "completed"},
                     "verify_effect": lambda _payload: {"status": "unavailable"},
                     "journal": events.append})

                attempt, = result["attempt_ledger"]
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(result["accounting"]["attempted_calls"], 1)
                self.assertEqual(result["accounting"]["completed_calls"], 0)
                self.assertEqual(attempt["call_id"], "turn-ledger-1")
                self.assertEqual(attempt["thread_id"], "thread-ledger-1")
                self.assertEqual(attempt["usage"], {
                    "input_tokens": 1234, "cached_input_tokens": 234,
                    "cache_write_input_tokens": 0, "output_tokens": 56,
                    "reasoning_output_tokens": 12})
                self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 1234)
                self.assertEqual(execute_calls, [])
                self.assertIsNone(result["task_effect"])
                self.assertIsNone(result["accounting"]["cost"])
                protocol = [json.loads(line) for line in
                            journal_path.read_text(encoding="utf-8").splitlines()]
                usage_events = [row["message"] for row in protocol
                                if row["direction"] == "received" and
                                row["message"].get("method") == "thread/tokenUsage/updated"]
                self.assertEqual(len(usage_events), 1)
                self.assertEqual(usage_events[0]["params"]["threadId"], attempt["thread_id"])
                self.assertEqual(usage_events[0]["params"]["turnId"], attempt["call_id"])
                self.assertTrue(any(event.get("event") == "model_attempt_finished" and
                                    event.get("thread_id") == attempt["thread_id"]
                                    for event in events))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)


if __name__ == "__main__":
    unittest.main()
