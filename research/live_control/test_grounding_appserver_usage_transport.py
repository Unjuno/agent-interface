"""Compose the real JSONL client with grounding and the adaptive attempt ledger."""
import json
import hashlib
import importlib.util
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
from research.live_control.v3_persistent_grounding_adapter_v1 import (
    V3PersistentGroundingAdapter,
)
from research.live_control.issue57_v3_attempt_ledger_v1 import (
    AppendOnlyAttemptLedger, make_row,
)
from research.live_control.issue57_v3_trace_adapter_v1 import project_task
from research.live_control.calc_durable_allocation_v1 import (
    DurableCalcAllocation, audit_allocation,
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
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                v3_model = V3PersistentGroundingAdapter(model)
                events = []
                execute_calls = []

                def anchor(_payload):
                    return v3_model(root / "call", "synthetic request", image,
                                    "compiled", workspace)

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
                comparison_row = make_row("provider-failure-arm-task-01", result,
                    {"status": "unavailable", "verified": False,
                     "keys_down": None, "buttons_down": None,
                     "evidence_ref": None, "evidence_digest": None},
                    {"status": "unavailable", "evidence_ref": None,
                     "evidence_digest": None})
                ledger = AppendOnlyAttemptLedger(
                    root / "issue57-attempts.jsonl",
                    ["provider-failure-arm-task-01"])
                ledger.append(comparison_row)
                ledger_audit = ledger.audit()
                self.assertEqual(ledger_audit["rows"], 1)
                self.assertEqual(ledger_audit["attempts"], 1)
                self.assertIsNone(comparison_row["task_effect"])
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(result["accounting"]["attempted_calls"], 1)
                self.assertEqual(result["accounting"]["completed_calls"], 0)
                self.assertEqual(attempt["call_id"], "turn-ledger-1")
                self.assertEqual(attempt["thread_id"], "thread-ledger-1")
                self.assertEqual(attempt["requested_model"], "synthetic-model")
                self.assertEqual(attempt["requested_effort"], "medium")
                self.assertEqual(attempt["usage"], {
                    "input_tokens": 1234, "cached_input_tokens": 234,
                    "cache_write_input_tokens": 0, "output_tokens": 56,
                    "reasoning_output_tokens": 12})
                failure_receipt = json.loads(
                    (root / "call" / "failure.json").read_text(encoding="utf-8"))
                self.assertEqual(failure_receipt["requested_model"],
                                 attempt["requested_model"])
                self.assertEqual(failure_receipt["requested_effort"],
                                 attempt["requested_effort"])
                self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 1234)
                projected = project_task("plain", 0, result,
                    {"submission_count": 0, "exact_submission": False},
                    {"local_observations": 1, "durable_calls": 1,
                     "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                     "releases_verified": False, "elapsed_ns": 1,
                     "source_to_completion_ns": None, "input_feedback_ns": [],
                     "repair": {"required": False, "old_reference_status": None,
                         "old_reference_pointer_admissions": 0,
                         "attempted": False, "succeeded": False}})
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"],
                    "failed_attempt_not_representable_in_v1")
                self.assertEqual(projected["caller_result"], result)
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
                sent = [row["message"] for row in protocol
                        if row["direction"] == "sent"]
                thread_start, = [row for row in sent if row["method"] == "thread/start"]
                turn_start, = [row for row in sent if row["method"] == "turn/start"]
                self.assertEqual(thread_start["params"]["model"],
                                 attempt["requested_model"])
                self.assertEqual(turn_start["params"]["effort"],
                                 attempt["requested_effort"])
                self.assertTrue(any(event.get("event") == "model_attempt_finished" and
                                    event.get("thread_id") == attempt["thread_id"]
                                    for event in events))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "app-server pipe transport requires Windows Python 3.12+")
    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_provider_transport_failure_is_retained_in_durable_g10_allocation(self):
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation

        with tempfile.TemporaryDirectory(prefix="grounding-durable-allocation-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic durable app-server composition fixture")
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", PEER], cwd=str(workspace),
                journal_path=str(root / "protocol.jsonl"))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                conditions = {"model": "synthetic-model", "effort": "medium",
                              "task": "two-cell-save", "route": "cold"}
                allocation_root = root / "allocations"
                allocation_root.mkdir()
                ledger = DurableCalcAllocation(
                    allocation_root, "attempt-provider-join-01",
                    source_sha256=hashlib.sha256(b"frozen task source").hexdigest(),
                    observation_ids=["observation-01"],
                    source_hashes={"caller.py": hashlib.sha256(
                        b"frozen caller source").hexdigest()},
                    conditions=conditions)
                journal = []
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "verify_effect": lambda _payload: {"status": "unavailable"},
                    "journal": journal.append,
                }
                spec = {
                    "target": "synthetic Calc task", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [],
                    "repair_on": [], "session_id": "durable-provider-fixture",
                }
                result = run_g10_in_durable_allocation(
                    spec, adapters, lambda _payload: {"interface_id": "unused"},
                    None, {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)

                receipt = audit_allocation(ledger.path)
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(receipt["status"], "audited")
                self.assertEqual(receipt["outcome"], "CALLER_FAILED")
                self.assertFalse(receipt["receipt_persisted"])
                self.assertFalse(receipt["effect_receipt_persisted"])
                attempt, = receipt["attempt_ledger"]
                self.assertEqual(attempt["status"], "failed")
                self.assertEqual(attempt["call_id"], "turn-ledger-1")
                self.assertEqual(attempt["thread_id"], "thread-ledger-1")
                self.assertEqual(attempt["requested_model"], "synthetic-model")
                self.assertEqual(attempt["requested_effort"], "medium")
                self.assertEqual(attempt["usage"], {
                    "input_tokens": 1234, "cached_input_tokens": 234,
                    "cache_write_input_tokens": 0, "output_tokens": 56,
                    "reasoning_output_tokens": 12})
                self.assertEqual(receipt["accounting"]["usage_totals"]["input_tokens"], 1234)
                self.assertTrue(any(event.get("event") == "model_attempt_finished" and
                                    event.get("call_id") == "turn-ledger-1"
                                    for event in journal))
                protocol = [json.loads(line) for line in
                    (root / "protocol.jsonl").read_text(encoding="utf-8").splitlines()]
                self.assertTrue(any(row["direction"] == "received" and
                    row["message"].get("method") == "thread/tokenUsage/updated" and
                    row["message"]["params"].get("turnId") == attempt["call_id"]
                    for row in protocol))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)


if __name__ == "__main__":
    unittest.main()
