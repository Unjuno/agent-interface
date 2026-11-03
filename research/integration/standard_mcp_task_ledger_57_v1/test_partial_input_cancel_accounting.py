"""Join a post-input Calc cancellation to exactly one provider attempt."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import runtime.cli_v1.test_mcp_owned_process as calc_tests
from app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall,
    parse_app_server_tool_request,
)
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_integrated_efficiency_model_call_v1 import (
    build_model_provider_call,
)
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from runtime.cli_v1.mcp_relay import Relay


class PartialInputCancelAccountingTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_after_first_transition_is_joined_without_replay(self):
        retained_root = os.environ.get(
            "AGENT_INTERFACE_RETAIN_CALC_CANCEL_LEDGER")
        retained_root = Path(retained_root).resolve() if retained_root else None
        if retained_root is not None and retained_root.exists():
            raise FileExistsError(retained_root)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image_path = root / "provider-observation.png"
            image_path.write_bytes(b"synthetic provider image placeholder")
            protocol_journal = root / "app-server" / "protocol.jsonl"
            protocol_journal.parent.mkdir()
            protocol_journal.write_bytes(
                b'{"direction":"received","message":{"method":"thread/started"}}\n')
            provider_call_root = root / "provider-call"
            recorder = ProviderAttemptRecorder(root / "provider-ledger")
            state = {"generation_join": None, "compiled_pending": None,
                     "control_results": [], "control_requests": [],
                     "control_count": 0,
                     "compiled_count": 0}
            original_create_server = calc_tests.create_server

            def create_recording_server(*args, **kwargs):
                server = original_create_server(*args, **kwargs)

                class ServerClient:
                    async def call_tool(self, name, arguments):
                        return await server.call_tool(name, arguments)

                caller = RecordedPublicMcpCaller(
                    Relay(ServerClient(), tools={
                        "interface_guarded_calc_compiled"}), recorder)

                class FakePlanner:
                    def __init__(self, answer):
                        self.answer = answer

                    def begin_turn(self, prompt, *, output_schema, image_path):
                        if (not prompt or output_schema != {"type": "object"}
                                or not Path(image_path).is_file()):
                            raise ValueError("invalid synthetic provider request")
                        return SimpleNamespace(thread_id="calc-cancel-thread-01",
                                               turn_id="calc-cancel-turn-01")

                    def await_turn(self, handle, timeout):
                        if timeout <= 0:
                            raise ValueError("bounded synthetic turn required")
                        usage = {"last": {
                            "inputTokens": 61, "outputTokens": 13,
                            "cachedInputTokens": 8, "cacheWriteInputTokens": 1,
                            "reasoningOutputTokens": 2}}
                        rows = (
                            {"direction": "received", "message": {
                                "method": "thread/tokenUsage/updated",
                                "params": {"threadId": handle.thread_id,
                                           "turnId": handle.turn_id,
                                           "tokenUsage": usage}}},
                            {"direction": "received", "message": {
                                "method": "turn/completed",
                                "params": {"threadId": handle.thread_id,
                                    "turn": {"id": handle.turn_id,
                                        "status": "completed", "items": [{
                                            "type": "agentMessage",
                                            "text": json.dumps(self.answer,
                                                sort_keys=True,
                                                separators=(",", ":"))}]}}}})
                        with protocol_journal.open("ab") as stream:
                            for row in rows:
                                stream.write(json.dumps(row,
                                    sort_keys=True,
                                    separators=(",", ":")).encode() + b"\n")
                        return SimpleNamespace(status="completed",
                            answer_eligible=True, answer=self.answer, usage=usage)

                class RecordingServer:
                    def __getattr__(self, name):
                        return getattr(server, name)

                    async def call_tool(self, name, arguments):
                        if name == "interface_guarded_calc_compiled":
                            state["compiled_count"] += 1
                            if state["compiled_count"] != 1:
                                raise AssertionError(
                                    "no consequential tool replay is allowed")
                            attempt_id = arguments.get("attempt_id")
                            if attempt_id != "calc-cancel-after-transition":
                                raise AssertionError(
                                    "unexpected attempt id for cancellation case")
                            planner = FakePlanner(arguments)
                            model_call = AppServerPublicMcpModelCall(
                                planner, protocol_journal, workspace=workspace,
                                contract="registered-calc-profile",
                                output_schema={"type": "object"},
                                model="synthetic-accounting-model", effort="low")
                            request_bytes, provider_call = build_model_provider_call(
                                model_call=model_call.call,
                                root=provider_call_root / "calc-cancel-attempt-01",
                                prompt="Execute the already reviewed Calc plan once.",
                                image=image_path,
                                contract="registered-calc-profile",
                                workspace=workspace)

                            def prepare_arguments(generation):
                                backend = generation["backend_result"]
                                parsed = parse_app_server_tool_request(
                                    generation["response_bytes"],
                                    thread_id=backend["thread_id"],
                                    turn_id=backend["turn_id"])
                                if parsed != arguments:
                                    raise AssertionError(
                                        "retained provider answer differs from tool request")
                                return parsed

                            joined = await caller.invoke_generation_to_tool(
                                "calc-cancel-after-transition",
                                request_bytes, provider_call,
                                "calc-provider-tool-call-01",
                                name, prepare_arguments)
                            if not joined["tool_call_submitted"]:
                                raise AssertionError(joined)
                            response_text = joined["tool_response"]["result"][
                                "content"][0]["text"]
                            state["generation_join"] = joined
                            state["compiled_pending"] = json.loads(response_text)
                            return SimpleNamespace(content=[SimpleNamespace(
                                text=response_text)])

                        state["control_count"] += 1
                        call_id = f"calc-cancel-control-{state['control_count']:03d}"
                        state["control_requests"].append({
                            "method": name, "arguments": arguments})
                        request_bytes = json.dumps({"tool": name,
                            "arguments": arguments}, sort_keys=True,
                            separators=(",", ":")).encode()

                        async def invoke_tool():
                            response = await server.call_tool(name, arguments)
                            response_value = response.model_dump(mode="json")
                            response_bytes = json.dumps(response_value,
                                sort_keys=True, separators=(",", ":")).encode()
                            return {"result": response_value,
                                    "response_bytes": response_bytes}

                        result = await recorder.invoke_tool_async(
                            None, call_id, name, request_bytes, invoke_tool)
                        state["control_results"].append({
                            "method": name, "call_id": call_id,
                            "result": result["content"][0]["text"]})
                        return SimpleNamespace(content=[SimpleNamespace(
                            text=result["content"][0]["text"])])

                return RecordingServer()

            fake_x_evidence = root / "fake-x-evidence"
            env = {"AGENT_INTERFACE_FAKE_X_EVIDENCE": str(fake_x_evidence)}
            with patch.dict(os.environ, env), patch.object(
                    calc_tests, "create_server", create_recording_server):
                cancellation_case = calc_tests.OwnedProcessMCPTests(
                    "test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown")
                await cancellation_case.test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown()

            self.assertIsNotNone(state["generation_join"])
            self.assertTrue(state["generation_join"]["tool_call_submitted"])
            self.assertEqual(state["compiled_pending"]["status"], "pending",
                             state["compiled_pending"])
            self.assertIsNone(state["compiled_pending"].get("task_success"))
            self.assertFalse(state["compiled_pending"].get("replay_allowed", False))
            compiled_call_id = state["compiled_pending"].get("call_id")
            cancel_requests = [row["arguments"] for row in
                state["control_requests"] if row["method"] ==
                "interface_guarded_cancel"]
            self.assertEqual(len(cancel_requests), 1, cancel_requests)
            self.assertEqual(cancel_requests[0].get("call_id"), compiled_call_id)
            self.assertEqual(state["compiled_count"], 1)

            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"], receipt)
            events = receipt["events"]
            attempts = [row for row in events if row["kind"] == "model_attempt"]
            tool_calls = [row for row in events if row["kind"] == "tool_call"]
            self.assertEqual(len(attempts), 1, attempts)
            attempt = attempts[0]
            self.assertEqual(attempt["attempt_id"],
                             "calc-cancel-after-transition")
            self.assertEqual(attempt["status"], "completed", attempt)
            self.assertEqual(attempt["usage"]["status"], "reported", attempt)
            self.assertEqual(attempt["usage"]["input_tokens"], 61, attempt)
            self.assertEqual(attempt["usage"]["output_tokens"], 13, attempt)
            compiled_calls = [row for row in tool_calls if row["method"] ==
                              "interface_guarded_calc_compiled"]
            self.assertEqual(len(compiled_calls), 1, compiled_calls)
            self.assertEqual(compiled_calls[0]["model_attempt_id"],
                             attempt["attempt_id"], compiled_calls[0])
            control_methods = {"interface_guarded_cancel", "interface_results",
                               "interface_close"}
            control_calls = [row for row in tool_calls
                             if row["method"] in control_methods]
            self.assertTrue(control_methods.issubset(
                {row["method"] for row in control_calls}), control_calls)
            self.assertTrue(all(row["model_attempt_id"] is None
                                for row in control_calls), control_calls)
            result_bodies = [json.loads(row["result"]) for row in
                state["control_results"] if row["method"] == "interface_results"]
            terminal = next((row for row in result_bodies
                if isinstance(row.get("cancellation"), dict) and
                row["cancellation"].get("status") != "pending"), None)
            self.assertIsNotNone(terminal, result_bodies)
            cleanup = terminal["cancellation"]["result"]
            self.assertEqual(cleanup["cleanup_status"], "UNKNOWN", cleanup)
            self.assertFalse(cleanup["release_confirmed"], cleanup)
            self.assertIsNone(cleanup["task_success"], cleanup)
            self.assertFalse(cleanup["replay_allowed"], cleanup)
            self.assertIsNone(terminal["task_success"], terminal)
            self.assertFalse(terminal["replay_allowed"], terminal)
            self.assertFalse(any(row["method"] in {
                "interface_guarded_input", "interface_guarded_recover_input"}
                for row in tool_calls), tool_calls)
            self.assertEqual(sum(row["method"] ==
                "interface_guarded_calc_compiled" for row in tool_calls), 1)

            retained = os.environ.get(
                "AGENT_INTERFACE_RETAIN_CALC_CANCEL_LEDGER")
            if retained:
                target = Path(retained).resolve()
                target.mkdir(parents=True, exist_ok=False)
                shutil.copytree(recorder.root, target / "provider-ledger")
                shutil.copytree(provider_call_root, target / "provider-call")
                shutil.copy2(protocol_journal, target / "app-server-protocol.jsonl")
                shutil.copytree(fake_x_evidence, target / "fake-x-evidence")
                (target / "reconciled-events.json").write_text(
                    json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
                (target / "joined-result.json").write_text(
                    json.dumps({"compiled_pending": state["compiled_pending"],
                        "cancel_terminal": terminal,
                        "control_methods": [row["method"] for row in control_calls],
                        "compiled_count": state["compiled_count"]},
                        sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
