import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall,
    parse_app_server_tool_request,
)
from ledger import summarize
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller


class AppServerProviderToPublicMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_spooled_host_may_create_protocol_journal_after_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "spool" / "protocol.jsonl"
            answer = {"tool": "interface_guarded_compiled", "arguments": {"value": 1}}
            usage = {"last": {"inputTokens": 21, "outputTokens": 8,
                "cachedInputTokens": 0, "cacheWriteInputTokens": 0,
                "reasoningOutputTokens": 1}}
            rows = [
                {"direction": "received", "message": {
                    "method": "thread/tokenUsage/updated", "params": {
                        "threadId": "thread-spool", "turnId": "turn-spool",
                        "tokenUsage": usage}}},
                {"direction": "received", "message": {
                    "method": "turn/completed", "params": {
                        "threadId": "thread-spool", "turn": {
                            "id": "turn-spool", "status": "completed",
                            "items": [{"type": "agentMessage", "text": json.dumps(answer)}]}}}},
            ]
            expected_bytes = b"".join(json.dumps(row, separators=(",", ":")).encode()+b"\n" for row in rows)

            class SpoolPlanner:
                def begin_turn(self, prompt, *, output_schema, image_path):
                    return SimpleNamespace(thread_id="thread-spool", turn_id="turn-spool")

                def await_turn(self, handle, timeout):
                    journal.parent.mkdir(parents=True, exist_ok=True)
                    journal.write_bytes(expected_bytes)
                    return SimpleNamespace(status="completed", answer_eligible=True,
                        answer=answer, error=None, usage=usage,
                        cancellation_requested=False, completed_agent_messages=1)

            model = AppServerPublicMcpModelCall(SpoolPlanner(), journal,
                workspace=workspace, contract="public-mcp", output_schema={"type": "object"},
                model="gpt-test", effort="low", path_converter=lambda path: str(path))
            result = model.call(root / "provider-attempt", "choose one tool", image,
                "public-mcp", workspace)
            self.assertEqual(result["raw"], answer)
            self.assertEqual((root / "provider-attempt" / "model" / "events.jsonl").read_bytes(),
                expected_bytes)
            self.assertEqual(result["usage"], {"input_tokens": 21,
                "cached_input_tokens": 0, "cache_write_input_tokens": 0,
                "output_tokens": 8, "reasoning_output_tokens": 1})

    async def test_app_server_turn_bytes_join_usage_and_public_tool_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "session" / "protocol.jsonl"
            journal.parent.mkdir()
            prefix = b'{"direction":"received","message":{"method":"thread/started"}}\n'
            journal.write_bytes(prefix)
            request_payload = {
                "method": "interface_guarded_compiled",
                "arguments": {"source_sequence": 4, "actions": []},
            }
            usage_row = {
                "direction": "received", "observed_ns": 9,
                "message": {"method": "thread/tokenUsage/updated", "params": {
                    "threadId": "thread-1", "turnId": "turn-1",
                    "tokenUsage": {"last": {
                        "inputTokens": 42, "outputTokens": 12,
                        "cachedInputTokens": 30, "cacheWriteInputTokens": 2,
                        "reasoningOutputTokens": 3}}}},
            }
            protocol_row = {
                "direction": "received", "observed_ns": 10,
                "message": {"method": "turn/completed", "params": {
                    "threadId": "thread-1", "turn": {
                        "id": "turn-1", "status": "completed",
                        "items": [{"type": "agentMessage",
                                   "text": json.dumps(request_payload)}]}}},
            }
            turn_bytes = b"".join(
                json.dumps(row, separators=(",", ":")).encode() + b"\n"
                for row in (usage_row, protocol_row))

            class FakePlanner:
                def begin_turn(self, prompt, *, output_schema, image_path):
                    self.received = (prompt, output_schema, image_path)
                    return SimpleNamespace(thread_id="thread-1", turn_id="turn-1")

                def await_turn(self, handle, timeout):
                    self.timeout = timeout
                    with journal.open("ab") as stream:
                        stream.write(turn_bytes)
                    return SimpleNamespace(
                        status="completed", answer_eligible=True,
                        answer=request_payload, error=None,
                        usage={"last": {
                            "inputTokens": 42, "outputTokens": 12,
                            "cachedInputTokens": 30, "cacheWriteInputTokens": 2,
                            "reasoningOutputTokens": 3}})

            planner = FakePlanner()
            model = AppServerPublicMcpModelCall(
                planner, journal, workspace=workspace, contract="public-mcp",
                output_schema={"type": "object"}, model="gpt-test", effort="low",
                path_converter=lambda path: str(path))
            recorder = ProviderAttemptRecorder(root / "ledger")

            class Relay:
                next_id = 1

                async def request(self, request_bytes):
                    request = json.loads(request_bytes)
                    self.requested = request
                    return {"id": request["id"], "tool": request["tool"],
                            "status": "returned", "result": {"ok": True}}

            relay = Relay()
            caller = RecordedPublicMcpCaller(relay, recorder)
            provider_request, provider_call = build_model_provider_call(
                model_call=model.call, root=root / "model-attempt",
                prompt="submit the exact visible task token", image=image,
                contract="public-mcp", workspace=workspace)

            def prepare_arguments(generation):
                return parse_app_server_tool_request(
                    generation["response_bytes"], thread_id="thread-1",
                    turn_id="turn-1")

            result = await caller.invoke_generation_to_tool(
                "attempt-1", provider_request, provider_call, "call-1",
                "interface_guarded_compiled", prepare_arguments)

            self.assertEqual(planner.received[0],
                             "submit the exact visible task token")
            self.assertEqual(planner.received[1], {"type": "object"})
            self.assertEqual(planner.received[2], str(image))
            self.assertEqual(planner.timeout, 90)
            self.assertEqual(result["generation"]["status"], "completed")
            self.assertEqual(result["generation"]["usage"], {
                "status": "reported", "input_tokens": 42, "output_tokens": 12,
                "cached_input_tokens": 30, "cache_write_input_tokens": 2,
                "reasoning_output_tokens": 3})
            self.assertEqual(relay.requested["tool"], "interface_guarded_compiled")
            self.assertEqual(relay.requested["arguments"], request_payload)
            raw = recorder.reconcile()
            self.assertTrue(raw["complete"])
            self.assertEqual([event["kind"] for event in raw["events"]],
                             ["model_attempt", "tool_call"])
            response_ref = next(ref for event in raw["events"]
                                if event["kind"] == "model_attempt"
                                for ref in event["raw_refs"]
                                if ref["path"].endswith("attempt-1.response.bin"))
            self.assertEqual((recorder.root / response_ref["path"]).read_bytes(),
                             turn_bytes)

    async def test_ineligible_turn_preserves_partial_usage_and_skips_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "session" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(b"")

            class FailedPlanner:
                def begin_turn(self, *_args, **_kwargs):
                    return SimpleNamespace(thread_id="thread-1", turn_id="turn-1")

                def await_turn(self, _handle, timeout):
                    usage = {"last": {"inputTokens": 13,
                                      "cachedInputTokens": 5}}
                    usage_row = {"direction": "received", "message": {
                        "method": "thread/tokenUsage/updated", "params": {
                            "threadId": "thread-1", "turnId": "turn-1",
                            "tokenUsage": usage}}}
                    error_row = {"direction": "received", "message": {
                        "method": "error"}}
                    with journal.open("ab") as stream:
                        for row in (usage_row, error_row):
                            stream.write(json.dumps(row).encode() + b"\n")
                    return SimpleNamespace(
                        status="failed", answer_eligible=False, answer=None,
                        error="provider failed", usage=usage)

            model = AppServerPublicMcpModelCall(
                FailedPlanner(), journal, workspace=workspace, contract="public-mcp",
                output_schema={"type": "object"}, model="gpt-test", effort="low",
                path_converter=str)
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request_bytes):
                    raise AssertionError("failed model turn must not reach public MCP")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            request, provider = build_model_provider_call(
                model_call=model.call, root=root / "failed-attempt", prompt="task",
                image=image, contract="public-mcp", workspace=workspace)
            result = await caller.invoke_generation_to_tool(
                "failed-attempt", request, provider, "call-failed",
                "interface_guarded_compiled", json.loads)

            self.assertFalse(result["tool_call_submitted"])
            self.assertEqual(result["generation"]["status"], "failed")
            self.assertEqual(result["generation"]["usage"], {
                "status": "partial", "input_tokens": 13,
                "output_tokens": None, "cached_input_tokens": 5})
            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"])
            self.assertEqual([event["kind"] for event in receipt["events"]],
                             ["model_attempt"])

    async def test_missing_turn_preserves_journal_partial_usage_and_skips_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "session" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(b"")

            class MissingTurnPlanner:
                def begin_turn(self, *_args, **_kwargs):
                    return SimpleNamespace(thread_id="thread-none", turn_id="turn-none")

                def await_turn(self, _handle, timeout):
                    usage_row = {"direction": "received", "message": {
                        "method": "thread/tokenUsage/updated", "params": {
                            "threadId": "thread-none", "turnId": "turn-none",
                            "tokenUsage": {"last": {
                                "inputTokens": 17, "cachedInputTokens": 4}}}}}
                    with journal.open("ab") as stream:
                        stream.write(json.dumps(usage_row).encode() + b"\n")
                    return None

            model = AppServerPublicMcpModelCall(
                MissingTurnPlanner(), journal, workspace=workspace,
                contract="public-mcp", output_schema={"type": "object"},
                model="gpt-test", effort="low", path_converter=str)
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                async def request(self, _request_bytes):
                    raise AssertionError("missing model turn must not reach public MCP")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            request, provider = build_model_provider_call(
                model_call=model.call, root=root / "missing-turn", prompt="task",
                image=image, contract="public-mcp", workspace=workspace)
            result = await caller.invoke_generation_to_tool(
                "missing-turn", request, provider, "call-missing-turn",
                "interface_guarded_compiled", json.loads)

            self.assertFalse(result["tool_call_submitted"])
            self.assertEqual(result["generation"]["status"], "failed")
            self.assertEqual(result["generation"]["usage"], {
                "status": "partial", "input_tokens": 17,
                "output_tokens": None, "cached_input_tokens": 4})
            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"])
            self.assertEqual([event["kind"] for event in receipt["events"]],
                             ["model_attempt"])
            self.assertEqual(receipt["events"][0]["usage"],
                             result["generation"]["usage"])

    async def test_timeout_preserves_partial_protocol_usage_and_skips_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "session" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(b"")
            usage_row = {"direction": "received", "message": {
                "method": "thread/tokenUsage/updated", "params": {
                    "threadId": "thread-timeout", "turnId": "turn-timeout",
                    "tokenUsage": {"last": {
                        "inputTokens": 19, "outputTokens": 3,
                        "cachedInputTokens": 7}}}}}
            complete = json.dumps(usage_row).encode() + b"\n"

            class TimedOutPlanner:
                def begin_turn(self, *_args, **_kwargs):
                    return SimpleNamespace(thread_id="thread-timeout",
                                           turn_id="turn-timeout")

                def await_turn(self, _handle, timeout):
                    with journal.open("ab") as stream:
                        stream.write(complete)
                        stream.write(b'{"direction":"received","message":')
                    raise TimeoutError("turn deadline elapsed")

            model = AppServerPublicMcpModelCall(
                TimedOutPlanner(), journal, workspace=workspace,
                contract="public-mcp", output_schema={"type": "object"},
                model="gpt-test", effort="low")
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request_bytes):
                    raise AssertionError("timed-out turn must not reach public MCP")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            request, provider = build_model_provider_call(
                model_call=model.call, root=root / "timeout-attempt",
                prompt="task", image=image, contract="public-mcp",
                workspace=workspace)
            result = await caller.invoke_generation_to_tool(
                "timeout-attempt", request, provider, "call-timeout",
                "interface_guarded_compiled", json.loads)

            self.assertFalse(result["tool_call_submitted"])
            generation = result["generation"]
            self.assertEqual(generation["status"], "timeout")
            self.assertEqual(generation["usage"], {
                "status": "partial", "input_tokens": 19,
                "output_tokens": 3, "cached_input_tokens": 7})
            self.assertIn(complete, generation["response_bytes"])
            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"])
            self.assertEqual([event["kind"] for event in receipt["events"]],
                             ["model_attempt"])
            self.assertEqual(receipt["events"][0]["usage"], generation["usage"])
            summary = summarize(receipt["events"])
            self.assertEqual(summary["usage_status"], "incomplete")
            self.assertIsNone(summary["input_tokens"])

    async def test_usage_mismatch_with_protocol_journal_skips_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"synthetic image")
            journal = root / "session" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(b"")
            payload = {"method": "interface_guarded_compiled", "arguments": {}}

            class MismatchedPlanner:
                def begin_turn(self, *_args, **_kwargs):
                    return SimpleNamespace(thread_id="thread-mismatch",
                                           turn_id="turn-mismatch")

                def await_turn(self, _handle, timeout):
                    rows = [
                        {"direction": "received", "message": {
                            "method": "thread/tokenUsage/updated", "params": {
                                "threadId": "thread-mismatch", "turnId": "turn-mismatch",
                                "tokenUsage": {"last": {
                                    "inputTokens": 7, "outputTokens": 3,
                                    "cachedInputTokens": 0, "cacheWriteInputTokens": 0,
                                    "reasoningOutputTokens": 1}}}}},
                        {"direction": "received", "message": {
                            "method": "turn/completed", "params": {
                                "threadId": "thread-mismatch", "turn": {
                                    "id": "turn-mismatch", "status": "completed",
                                    "items": [{"type": "agentMessage",
                                               "text": json.dumps(payload)}]}}}},
                    ]
                    with journal.open("ab") as stream:
                        for row in rows:
                            stream.write(json.dumps(row).encode() + b"\n")
                    return SimpleNamespace(
                        status="completed", answer_eligible=True, answer=payload,
                        usage={"last": {
                            "inputTokens": 8, "outputTokens": 3,
                            "cachedInputTokens": 0, "cacheWriteInputTokens": 0,
                            "reasoningOutputTokens": 1}})

            model = AppServerPublicMcpModelCall(
                MismatchedPlanner(), journal, workspace=workspace,
                contract="public-mcp", output_schema={"type": "object"},
                model="gpt-test", effort="low")
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request_bytes):
                    raise AssertionError("inconsistent usage must not reach public MCP")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            request, provider = build_model_provider_call(
                model_call=model.call, root=root / "mismatched-attempt",
                prompt="task", image=image, contract="public-mcp",
                workspace=workspace)
            result = await caller.invoke_generation_to_tool(
                "mismatched-attempt", request, provider, "call-mismatch",
                "interface_guarded_compiled", json.loads)

            self.assertFalse(result["tool_call_submitted"])
            self.assertEqual(result["generation"]["status"], "failed")
            self.assertEqual(result["generation"]["error_type"], "ValueError")
            self.assertIn(b"thread/tokenUsage/updated",
                          result["generation"]["response_bytes"])
            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"])
            self.assertEqual([event["kind"] for event in receipt["events"]],
                             ["model_attempt"])


if __name__ == "__main__":
    unittest.main()
