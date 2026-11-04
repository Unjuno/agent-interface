"""Join a post-input Calc cancellation to exactly one provider attempt."""

import asyncio
import json
import os
import shutil
import tempfile
import time
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

    async def test_generic_compiled_partial_input_cancel_polls_same_call_in_ledger(self):
        retained = os.environ.get(
            "AGENT_INTERFACE_RETAIN_PARTIAL_PENDING_COMPOSITION")
        retained = Path(retained).resolve() if retained else None
        if retained is not None and retained.exists():
            raise FileExistsError(retained)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            (server_root / "compiled-profile-mode").write_text("enabled")
            calc_tests._write_json(server_root / "supervisor-fake-x.json", {
                "down": [], "effects": [], "refused": []})
            recorder = ProviderAttemptRecorder(root / "provider-ledger")
            server = calc_tests.create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True, guarded_prestarted_cancel_supervisor=True,
                _guarded_cancel_supervisor_target=(
                    calc_tests._fake_prestarted_cancel_worker),
                _guarded_owner_factory=calc_tests._fake_owner_factory)

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
            controls = []
            closed = False

            async def public_call(call_id, name, arguments):
                controls.append({"call_id": call_id, "method": name,
                                 "arguments": arguments})
                return await caller.call_tool(None, call_id, name, arguments)

            def body(response):
                return json.loads(response["result"]["content"][0]["text"])

            try:
                observed = body(await public_call(
                    "observe-01", "interface_guarded_observe", {}))
                source = observed["source"]
                minted = body(await public_call("mint-01",
                    "interface_guarded_mint", {
                        "alias": "field", "source_sequence": source["sequence"],
                        "point": [8, 8], "region_size": [12, 12]}))
                payload = calc_tests._compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                payload["wait_for_result_ms"] = 0
                answer = json.dumps(payload, sort_keys=True,
                                    separators=(",", ":")).encode()
                (server_root / "block-owner-io").write_text("block")

                async def provider_call():
                    return {"status": "completed", "usage": {
                        "status": "reported", "input_tokens": 61,
                        "output_tokens": 13, "cached_input_tokens": 8,
                        "reasoning_output_tokens": 2}, "response_bytes": answer}

                joined = await caller.invoke_generation_to_tool(
                    "partial-input-attempt-01", b"synthetic provider request",
                    provider_call, "compiled-tool-01",
                    "interface_guarded_compiled",
                    lambda generation: json.loads(generation["response_bytes"]))
                self.assertTrue(joined["tool_call_submitted"], joined)
                pending = body(joined["tool_response"])
                self.assertEqual(pending.get("status"), "pending", pending)
                call_id = pending["call_id"]

                deadline = time.monotonic() + 3
                while (not (server_root / "owner-io-entered.json").exists()
                       and time.monotonic() < deadline):
                    await asyncio.sleep(0.005)
                self.assertTrue((server_root / "owner-io-entered.json").exists())
                down = json.loads((server_root / "owner-io-entered.json").read_text())
                self.assertTrue(down, "cancel must occur while input is held down")
                calc_tests._write_json(server_root / "supervisor-fake-x.json", {
                    "down": down, "effects": [], "refused": []})
                (server_root / "block-cleanup-supervisor").write_text("block")

                cancel = body(await public_call("cancel-01",
                    "interface_guarded_cancel", {"call_id": call_id}))
                self.assertEqual(cancel.get("status"), "pending", cancel)
                self.assertEqual(cancel.get("cancellation", {}).get("status"),
                                 "pending", cancel)
                self.assertEqual(cancel.get("call_id"), call_id, cancel)
                operation_id = cancel.get("operation_id")
                self.assertIsInstance(operation_id, str, cancel)
                self.assertEqual(cancel.get("cancellation", {}).get(
                    "operation_id"), operation_id, cancel)
                (server_root / "continue-cleanup-supervisor").write_text("continue")

                polls = []
                deadline = time.monotonic() + 6
                while time.monotonic() < deadline:
                    result = body(await public_call(
                        f"results-{len(polls) + 1:03d}", "interface_results",
                        {"call_id": call_id, "include_image": False}))
                    polls.append(result)
                    cancellation = result.get("cancellation")
                    if (isinstance(cancellation, dict) and
                            cancellation.get("status") != "pending"):
                        break
                    await asyncio.sleep(0.05)
                else:
                    self.fail("same cancellation did not reach a terminal receipt")

                terminal = polls[-1]
                self.assertEqual(terminal.get("call_id"), call_id, terminal)
                self.assertEqual(terminal["cancellation"].get("operation_id"),
                                 operation_id, terminal)
                cleanup = terminal["cancellation"].get("result", {})
                self.assertTrue(cleanup.get("owner_process_retired"), cleanup)
                self.assertEqual(cleanup.get("cleanup_status"), "UNKNOWN", cleanup)
                self.assertFalse(cleanup.get("release_confirmed"), cleanup)
                self.assertIsNone(terminal.get("task_success"), terminal)
                self.assertFalse(terminal.get("replay_allowed"), terminal)

                fake_x_after = json.loads(
                    (server_root / "supervisor-fake-x.json").read_text())
                self.assertEqual(fake_x_after["down"], [])
                await public_call("close-01", "interface_close", {})
                closed = True
                receipt = recorder.reconcile()
                self.assertTrue(receipt["complete"], receipt)
                attempts = [row for row in receipt["events"]
                            if row["kind"] == "model_attempt"]
                tools = [row for row in receipt["events"]
                         if row["kind"] == "tool_call"]
                self.assertEqual(len(attempts), 1, attempts)
                self.assertEqual(attempts[0]["attempt_id"],
                                 "partial-input-attempt-01")
                self.assertEqual(attempts[0]["usage"]["input_tokens"], 61)
                self.assertEqual(attempts[0]["usage"]["output_tokens"], 13)
                self.assertEqual(sum(row["method"] ==
                    "interface_guarded_compiled" for row in tools), 1)
                compiled_event = next(row for row in tools
                                      if row["method"] ==
                                      "interface_guarded_compiled")
                self.assertEqual(compiled_event.get("model_attempt_id"),
                                 "partial-input-attempt-01", compiled_event)
                self.assertEqual(sum(row["method"] in {
                    "interface_guarded_input", "interface_guarded_recover_input"}
                    for row in tools), 0)
                self.assertEqual(sum(row["method"] == "interface_guarded_cancel"
                                     for row in tools), 1)
                self.assertEqual(sum(row["method"] == "interface_results"
                                     for row in tools), len(polls))
                self.assertEqual(sum(row["method"] == "interface_close"
                                     for row in tools), 1)
                poll_requests = [row["arguments"] for row in controls
                                 if row["method"] == "interface_results"]
                self.assertTrue(all(row.get("call_id") == call_id
                                    for row in poll_requests), poll_requests)
                unlinked_controls = [row for row in tools if row["method"] in {
                    "interface_guarded_cancel", "interface_results",
                    "interface_close"}]
                self.assertTrue(all(row.get("model_attempt_id") is None
                                    for row in unlinked_controls), unlinked_controls)
                self.assertTrue(all(row["call_id"] == call_id for row in polls))
            finally:
                (server_root / "resume-owner-io").write_text("resume")
                (server_root / "continue-cleanup-supervisor").write_text("continue")
                if not closed:
                    try:
                        await public_call("close-01", "interface_close", {})
                    except Exception:
                        await server.call_tool("interface_close", {})

            if retained is not None:
                retained.mkdir(parents=True, exist_ok=False)
                shutil.copytree(recorder.root, retained / "provider-ledger")
                shutil.copy2(server_root / "supervisor-fake-x.json",
                             retained / "supervisor-fake-x.json")
                shutil.copy2(server_root / "owner-io-entered.json",
                             retained / "owner-io-entered.json")
                (retained / "reconciled-events.json").write_text(
                    json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
                (retained / "joined-result.json").write_text(json.dumps({
                    "compiled_pending": pending, "cancel_response": cancel,
                    "cancel_operation_id": operation_id,
                    "result_poll_call_ids": [row["arguments"]["call_id"]
                        for row in controls if row["method"] == "interface_results"],
                    "result_poll_statuses": [row.get("cancellation", {}).get("status")
                                             for row in polls],
                    "cancel_terminal": terminal,
                    "input_keys_before_cancel": down,
                    "cleanup_fake_x_after": fake_x_after},
                    sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
