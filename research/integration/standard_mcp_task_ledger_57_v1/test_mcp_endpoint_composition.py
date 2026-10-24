import asyncio
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall,
    parse_app_server_tool_request,
)
from ledger import summarize
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from recorded_integrated_efficiency_model_call_v1 import (
    build_model_provider_call,
    parse_agent_message,
)
from runtime.cli_v1.mcp_relay import Relay
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_owned_process import (
    _compiled_profile_payload,
    _fake_owner_factory,
    _preserve_fake_x_run,
    metadata,
)


def _reviewable_fake_owner_factory(targets, directory, display_name, options):
    owner = _fake_owner_factory(targets, directory, display_name, options)
    owner.get()
    owner.bridge.backend.d.create_resource_object = lambda _kind, window_id: (
        SimpleNamespace(id=window_id))
    generation_path = Path(directory) / "fake-process-generation"
    identity_patch = patch(
        "runtime.guarded_x11_v1.bridge.read_linux_x11_process_identity",
        side_effect=lambda _connection, _window_id: (
            generation_path.read_text(encoding="utf-8")
            if generation_path.exists() else "a" * 64))
    identity_patch.start()
    owner._owned_process_test_cleanup.addCleanup(identity_patch.stop)
    return owner


class ProviderToPublicMcpCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_stale_review_receipt_does_not_start_second_attempt(self):
        initial_body = {
            "method_receipt": {
                "outcome": "SAFE_YIELD", "reason": "association_changed",
                "completed_transitions": 0,
                "critical_events": [{
                    "event": "admission_refused",
                    "status": "association_changed",
                }],
            },
            "session": {
                "recovery_required": False,
                "owner_input_obligations_source": "child_rpc_snapshot",
                "owner_input_obligations": {"keys": {}, "buttons": []},
                "owner_process": {"alive": True, "retired": False},
            },
        }
        initial_response = {
            "status": "returned", "tool": "interface_guarded_compiled",
            "result": {"content": [{"text": json.dumps(initial_body)}]},
        }
        refused_review = {
            "status": "returned", "tool": "interface_guarded_review_window",
            "result": {"content": [{"text": json.dumps({"status": "refused"})}]},
        }
        caller = object.__new__(RecordedPublicMcpCaller)
        invocations = []

        async def initial_only(*args):
            invocations.append(args)
            return {"tool_call_submitted": True,
                    "tool_response": initial_response}

        caller.invoke_generation_to_tool = initial_only

        async def stale_recovery_plan(_initial):
            return {
                "attempt_id": "attempt-2", "request_bytes": b"replan",
                "provider_call": lambda: self.fail("provider must not be called"),
                "call_id": "call-2", "method": "interface_guarded_compiled",
                "prepare_arguments": lambda generation: generation,
                "review_response": refused_review,
                "target_response": refused_review,
            }

        result = await caller.invoke_generation_to_tool_with_one_safe_recovery(
            "attempt-1", b"request", lambda: self.fail("initial is stubbed"),
            "call-1", "interface_guarded_compiled", lambda generation: generation,
            stale_recovery_plan)

        self.assertFalse(result["recovery_started"])
        self.assertIsNone(result["recovery"])
        self.assertEqual(result["review"], refused_review)
        self.assertEqual(len(invocations), 1)

    async def test_replanned_arguments_must_bind_fresh_mint_before_dispatch(self):
        owner = {"pid": 1234, "alive": True, "retired": False}
        session = {
            "owner_process": owner, "review_required": False,
            "recovery_required": False,
            "owner_input_obligations_source": "child_rpc_snapshot",
            "owner_input_obligations": {"keys": {}, "buttons": []},
            "compiled_scope": "scope-1", "compiled_surface": "surface-1",
        }

        def response(tool, body):
            return {"status": "returned", "tool": tool,
                    "result": {"content": [{"text": json.dumps(body)}]}}

        stale_payload = {"interface": {"symbols": {
            "field": {"target_reference": "field"}}}}
        initial = {
            "tool_call_submitted": True,
            "tool_response": response("interface_guarded_compiled", {
                "method_receipt": {
                    "outcome": "SAFE_YIELD", "reason": "association_changed",
                    "completed_transitions": 0,
                    "critical_events": [{"event": "admission_refused",
                                         "status": "association_changed"}],
                },
                "session": {**session, "observation_sequence": 1},
            }),
            "generation": {"response_bytes": json.dumps(
                stale_payload).encode("utf-8")},
        }
        reviewed = response("interface_guarded_review_window", {
            "status": "reviewed", "input_dispatched": False,
            "source": {"sequence": 2, "pointer_binding": {
                "process_generation": "b" * 64}},
            "session": session,
        })
        minted = response("interface_guarded_mint", {
            "status": "minted", "input_dispatched": False,
            "alias": "field_fresh", "offset": [8, 8], "source_sequence": 2,
            "session": session,
        })
        caller = object.__new__(RecordedPublicMcpCaller)
        invoke_rows = []
        dispatched = []

        async def invoke(*args):
            invoke_rows.append(args)
            if len(invoke_rows) == 1:
                return initial
            arguments = args[5]({"response_bytes": json.dumps({
                "interface": {
                    "session_scope": "scope-1", "surface": "surface-1",
                    "symbols": {"field": {"target_reference": "field"}},
                    "actions": {"enter": {"target_symbol": "field"}},
                },
                "bindings": {"enter": {"offset": [8, 8]}},
            }).encode("utf-8")})
            dispatched.append(arguments)
            return {"tool_call_submitted": True}

        caller.invoke_generation_to_tool = invoke

        async def replan(_initial):
            return {
                "attempt_id": "attempt-2", "request_bytes": b"replan",
                "provider_call": lambda: {"status": "completed"},
                "call_id": "call-2", "method": "interface_guarded_compiled",
                "prepare_arguments": lambda generation: json.loads(
                    generation["response_bytes"]),
                "review_response": reviewed, "target_response": minted,
            }

        with self.assertRaisesRegex(ValueError, "do not bind the reviewed target"):
            await caller.invoke_generation_to_tool_with_one_safe_recovery(
                "attempt-1", b"initial", lambda: None, "call-1",
                "interface_guarded_compiled", lambda generation: generation,
                replan)
        self.assertEqual(len(invoke_rows), 2)
        self.assertEqual(dispatched, [])

    async def test_preinput_refusal_requires_fresh_review_before_one_replan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            (server_root / "compiled-profile-mode").write_text("enabled")
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_reviewable_fake_owner_factory,
            )

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
            provider_calls = 0
            recovery_calls = 0
            try:
                first_observation = await caller.call_tool(
                    None, "observe-before-stale", "interface_guarded_observe", {})
                first = json.loads(first_observation["result"]["content"][0]["text"])
                self.assertIn("source", first, repr(first))
                first_target = json.loads((await caller.call_tool(
                    None, "mint-before-stale", "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": first["source"]["sequence"],
                        "point": [8, 8], "region_size": [12, 12],
                    }))["result"]["content"][0]["text"])["offset"]
                first_payload = _compiled_profile_payload(
                    first["session"]["compiled_scope"],
                    first["session"]["compiled_surface"], first_target)
                first_payload["wait_for_result_ms"] = 10000
                first_bytes = json.dumps(
                    first_payload, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")

                async def provider(response_bytes):
                    nonlocal provider_calls
                    provider_calls += 1
                    return {"status": "completed", "response_bytes": response_bytes,
                            "usage": {"status": "reported", "input_tokens": 11,
                                      "output_tokens": 4}}

                def make_stale(generation):
                    (server_root / "fake-process-generation").write_text(
                        "b" * 64, encoding="utf-8")
                    return json.loads(generation["response_bytes"])

                async def reobserve_and_replan(first_result):
                    nonlocal recovery_calls
                    recovery_calls += 1
                    review_response = await caller.call_tool(
                        None, "recovery-window-review",
                        "interface_guarded_review_window", {"window_id": 20})
                    reviewed = json.loads(
                        review_response["result"]["content"][0]["text"])
                    self.assertEqual(reviewed["status"], "reviewed", reviewed)
                    self.assertGreater(reviewed["source"]["sequence"],
                                       first["source"]["sequence"])
                    self.assertEqual(
                        reviewed["source"]["pointer_binding"]["process_generation"],
                        "b" * 64)
                    minted_response = await caller.call_tool(
                        None, "mint-after-review", "interface_guarded_mint", {
                            "alias": "field_recovered",
                            "source_sequence": reviewed["source"]["sequence"],
                            "point": [8, 8], "region_size": [12, 12],
                        })
                    minted_body = json.loads(
                        minted_response["result"]["content"][0]["text"])
                    self.assertIn("offset", minted_body, repr(minted_body))
                    minted = minted_body["offset"]
                    payload = _compiled_profile_payload(
                        reviewed["session"]["compiled_scope"],
                        reviewed["session"]["compiled_surface"], minted)
                    payload["interface"]["symbols"]["field"][
                        "target_reference"] = "field_recovered"
                    payload["wait_for_result_ms"] = 10000
                    response_bytes = json.dumps(
                        payload, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8")
                    return {
                        "attempt_id": "replan-generation",
                        "request_bytes": b"fresh reviewed target and replan",
                        "provider_call": lambda: provider(response_bytes),
                        "call_id": "replan-compiled-call",
                        "method": "interface_guarded_compiled",
                        "prepare_arguments": lambda generation: json.loads(
                            generation["response_bytes"]),
                        "review_response": review_response,
                        "target_response": minted_response,
                    }

                result = await caller.invoke_generation_to_tool_with_one_safe_recovery(
                    "initial-generation", b"initial observed-target request",
                    lambda: provider(first_bytes), "initial-compiled-call",
                    "interface_guarded_compiled", make_stale,
                    reobserve_and_replan)

                self.assertTrue(result["recovery_started"], repr(
                    result["initial"]["tool_response"]))
                self.assertEqual(recovery_calls, 1)
                self.assertEqual(provider_calls, 2)
                self.assertEqual(result["review"]["status"], "returned")
                first_receipt = json.loads(
                    result["initial"]["tool_response"]["result"]["content"][0]["text"])
                self.assertEqual(first_receipt["method_receipt"]["outcome"],
                                 "SAFE_YIELD")
                self.assertEqual(first_receipt["method_receipt"]["reason"],
                                 "association_changed")
                self.assertEqual(first_receipt["method_receipt"]["completed_transitions"],
                                 0)
                admission = [event for event in first_receipt["method_receipt"][
                    "critical_events"] if event["event"] == "admission_refused"]
                self.assertEqual(len(admission), 1)
                self.assertEqual(admission[0]["status"], "association_changed")
                self.assertFalse(any(
                    event["event"] == "action_terminal"
                    for event in first_receipt["method_receipt"]["critical_events"]))
                self.assertIsNotNone(result["recovery"])
                second_receipt = json.loads(
                    result["recovery"]["tool_response"]["result"]["content"][0]["text"])
                self.assertEqual(second_receipt["method_receipt"]["outcome"],
                                 "TASK_SUCCEEDED", repr(second_receipt))
                self.assertEqual(second_receipt["method_receipt"]["completed_transitions"],
                                 1)
                self.assertIsNone(second_receipt["task_success"])
                self.assertFalse(second_receipt["replay_allowed"])
                release_events = [event for event in second_receipt["method_receipt"][
                    "critical_events"] if event["event"] == "action_terminal"]
                self.assertEqual(len(release_events), 1)
                self.assertTrue(release_events[0]["release_verified"])
                initial_state = (server_root /
                                 "synthetic-application-initial.rgb").read_bytes()
                final_state = (server_root /
                               "synthetic-application-state.rgb").read_bytes()
                task_success = Image.frombytes(
                    "RGB", (32, 32), final_state, "raw", "BGRX"
                ).getpixel((1, 1)) == (255, 0, 0)
                self.assertTrue(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success, final_state)
                self.assertFalse(
                    initial_state == final_state)
                summary = summarize(recorder.reconcile()["events"])
                self.assertEqual(summary["model_attempt_count"], 2)
                self.assertEqual(summary["tool_call_count"], 6)
                self.assertEqual(summary["input_tokens"], 22)
                self.assertEqual(summary["output_tokens"], 8)
                self.assertTrue(summary["task_success"])
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("fresh-review-replan-after-stale-generation", root)

    async def test_fake_app_server_turn_reaches_public_compiled_tool_and_effect_oracle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            (server_root / "compiled-profile-mode").write_text("enabled")
            workspace = root / "workspace"
            workspace.mkdir()
            image_path = root / "observation.png"
            image_path.write_bytes(b"synthetic observed image")
            journal = root / "app-server" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(
                b'{"direction":"received","message":{"method":"thread/started"}}\n')
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
            )

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
            try:
                observation = await caller.call_tool(
                    None, "observe-appserver", "interface_guarded_observe", {})
                observed = json.loads(
                    observation["result"]["content"][0]["text"])
                minted_call = await caller.call_tool(
                    None, "mint-appserver", "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": observed["source"]["sequence"],
                        "point": [8, 8], "region_size": [12, 12],
                    })
                minted = json.loads(
                    minted_call["result"]["content"][0]["text"])
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                payload["wait_for_result_ms"] = 10000
                initial_state = (
                    server_root / "synthetic-application-initial.rgb").read_bytes()
                initial_pixel = Image.frombytes(
                    "RGB", (32, 32), initial_state, "raw", "BGRX").getpixel((1, 1))
                self.assertNotEqual(initial_pixel, (255, 0, 0))
                completed_text = json.dumps(payload, separators=(",", ":"))

                class FakePlanner:
                    def begin_turn(self, prompt, *, output_schema, image_path):
                        self.asserted_call = (prompt, output_schema, image_path)
                        return SimpleNamespace(thread_id="thread-appserver",
                                               turn_id="turn-appserver")

                    def await_turn(self, handle, timeout):
                        usage = {"last": {
                            "inputTokens": 42, "outputTokens": 12,
                            "cachedInputTokens": 30, "cacheWriteInputTokens": 2,
                            "reasoningOutputTokens": 3}}
                        usage_row = {"direction": "received", "observed_ns": 19,
                                     "message": {
                                         "method": "thread/tokenUsage/updated",
                                         "params": {"threadId": handle.thread_id,
                                                    "turnId": handle.turn_id,
                                                    "tokenUsage": usage}}}
                        row = {"direction": "received", "observed_ns": 20,
                               "message": {"method": "turn/completed", "params": {
                                   "threadId": handle.thread_id, "turn": {
                                       "id": handle.turn_id, "status": "completed",
                                       "items": [{"type": "agentMessage",
                                                  "text": completed_text}]}}}}
                        with journal.open("ab") as stream:
                            for event in (usage_row, row):
                                stream.write(json.dumps(
                                    event, separators=(",", ":")).encode() + b"\n")
                        return SimpleNamespace(
                            status="completed", answer_eligible=True,
                            answer=payload, usage=usage)

                planner = FakePlanner()
                model = AppServerPublicMcpModelCall(
                    planner, journal, workspace=workspace, contract="public-mcp",
                    output_schema={"type": "object"}, model="synthetic-app-server",
                    effort="low")
                request, provider = build_model_provider_call(
                    model_call=model.call, root=root / "model-attempt",
                    prompt="apply the visible synthetic target", image=image_path,
                    contract="public-mcp", workspace=workspace)
                result = await caller.invoke_generation_to_tool(
                    "appserver-generation", request, provider,
                    "appserver-compiled-call", "interface_guarded_compiled",
                    lambda generation: parse_app_server_tool_request(
                        generation["response_bytes"], thread_id="thread-appserver",
                        turn_id="turn-appserver"))

                self.assertTrue(result["tool_call_submitted"], result["generation"])
                self.assertEqual(result["generation"]["usage"]["input_tokens"], 42)
                self.assertEqual(result["generation"]["usage"]["reasoning_output_tokens"], 3)
                self.assertEqual(
                    result["generation"]["response_bytes"],
                    journal.read_bytes().split(b"\n", 1)[1])
                method_receipt = json.loads(
                    result["tool_response"]["result"]["content"][0]["text"])
                self.assertEqual(method_receipt["method_receipt"]["outcome"],
                                 "TASK_SUCCEEDED")
                self.assertIsNone(method_receipt["task_success"])
                self.assertFalse(method_receipt["replay_allowed"])

                final_state = (
                    server_root / "synthetic-application-state.rgb").read_bytes()
                final_pixel = Image.frombytes(
                    "RGB", (32, 32), final_state, "raw", "BGRX").getpixel((1, 1))
                task_success = final_pixel == (255, 0, 0)
                self.assertTrue(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success, final_state)
                receipt = recorder.reconcile()
                summary = summarize(receipt["events"])
                self.assertTrue(receipt["complete"])
                self.assertEqual(summary["model_attempt_count"], 1)
                self.assertEqual(summary["tool_call_count"], 3)
                self.assertEqual(summary["input_tokens"], 42)
                self.assertEqual(summary["output_tokens"], 12)
                self.assertTrue(summary["task_success"])
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("appserver-public-mcp-success", root)

    async def test_fake_app_server_stale_target_is_refused_by_public_compiled_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            (server_root / "compiled-profile-mode").write_text("enabled")
            workspace = root / "workspace"
            workspace.mkdir()
            image_path = root / "observation.png"
            image_path.write_bytes(b"synthetic observed image")
            journal = root / "app-server" / "protocol.jsonl"
            journal.parent.mkdir()
            journal.write_bytes(b"")
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
            )

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
            try:
                observation = await caller.call_tool(
                    None, "observe-stale-appserver", "interface_guarded_observe", {})
                observed = json.loads(
                    observation["result"]["content"][0]["text"])
                minted_call = await caller.call_tool(
                    None, "mint-stale-appserver", "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": observed["source"]["sequence"],
                        "point": [8, 8], "region_size": [12, 12],
                    })
                minted = json.loads(
                    minted_call["result"]["content"][0]["text"])
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                initial_state = (
                    server_root / "synthetic-application-initial.rgb").read_bytes()
                payload["wait_for_result_ms"] = 10000
                completed_text = json.dumps(payload, separators=(",", ":"))

                class FakePlanner:
                    def begin_turn(self, _prompt, *, output_schema, image_path):
                        self.asserted_call = (output_schema, image_path)
                        return SimpleNamespace(thread_id="thread-stale-appserver",
                                               turn_id="turn-stale-appserver")

                    def await_turn(self, handle, timeout):
                        usage = {"last": {
                            "inputTokens": 40, "outputTokens": 9,
                            "cachedInputTokens": 20, "cacheWriteInputTokens": 1,
                            "reasoningOutputTokens": 2}}
                        usage_row = {"direction": "received", "observed_ns": 29,
                                     "message": {
                                         "method": "thread/tokenUsage/updated",
                                         "params": {"threadId": handle.thread_id,
                                                    "turnId": handle.turn_id,
                                                    "tokenUsage": usage}}}
                        row = {"direction": "received", "observed_ns": 30,
                               "message": {"method": "turn/completed", "params": {
                                   "threadId": handle.thread_id, "turn": {
                                       "id": handle.turn_id, "status": "completed",
                                       "items": [{"type": "agentMessage",
                                                  "text": completed_text}]}}}}
                        with journal.open("ab") as stream:
                            for event in (usage_row, row):
                                stream.write(json.dumps(
                                    event, separators=(",", ":")).encode() + b"\n")
                        return SimpleNamespace(
                            status="completed", answer_eligible=True,
                            answer=payload, usage=usage)

                model = AppServerPublicMcpModelCall(
                    FakePlanner(), journal, workspace=workspace,
                    contract="public-mcp", output_schema={"type": "object"},
                    model="synthetic-app-server", effort="low")
                request, provider = build_model_provider_call(
                    model_call=model.call, root=root / "stale-model-attempt",
                    prompt="act on the just observed target", image=image_path,
                    contract="public-mcp", workspace=workspace)

                def change_generation_after_provider(generation):
                    (server_root / "fake-process-generation").write_text(
                        "b" * 64, encoding="utf-8")
                    return parse_app_server_tool_request(
                        generation["response_bytes"],
                        thread_id="thread-stale-appserver",
                        turn_id="turn-stale-appserver")

                composed = await caller.invoke_generation_to_tool(
                    "stale-appserver-generation", request, provider,
                    "stale-appserver-call", "interface_guarded_compiled",
                    change_generation_after_provider)
                self.assertTrue(composed["tool_call_submitted"])
                self.assertEqual(composed["generation"]["status"], "completed")
                result = json.loads(
                    composed["tool_response"]["result"]["content"][0]["text"])
                self.assertEqual(result["method_receipt"]["outcome"], "SAFE_YIELD")
                self.assertEqual(result["method_receipt"]["reason"],
                                 "execution_refused")
                self.assertEqual(result["method_receipt"]["completed_transitions"], 0)
                self.assertIsNone(result["task_success"])
                self.assertFalse(result["replay_allowed"])
                self.assertFalse(
                    (server_root / "synthetic-application-state.rgb").exists())

                task_success = Image.frombytes(
                    "RGB", (32, 32), initial_state, "raw", "BGRX"
                ).getpixel((1, 1)) == (255, 0, 0)
                self.assertFalse(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success, initial_state)
                receipt = recorder.reconcile()
                summary = summarize(receipt["events"])
                self.assertTrue(receipt["complete"])
                self.assertEqual(summary["model_attempt_count"], 1)
                self.assertEqual(summary["tool_call_count"], 3)
                self.assertEqual(summary["input_tokens"], 40)
                self.assertEqual(summary["output_tokens"], 9)
                self.assertFalse(summary["task_success"])
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("appserver-public-mcp-stale-generation", root)

    async def test_failed_provider_generation_is_not_sent_to_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request_bytes):
                    raise AssertionError("failed generation must not reach Relay")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)

            async def failed_provider():
                return {"status": "failed",
                        "usage": {"status": "unavailable",
                                  "input_tokens": None,
                                  "output_tokens": None},
                        "response_bytes": None}

            result = await caller.invoke_generation_to_tool(
                "generation-failed", b"provider-request", failed_provider,
                "tool-after-failure", "interface_guarded_compiled", json.loads)

            self.assertFalse(result["tool_call_submitted"])
            self.assertEqual(result["generation"]["status"], "failed")
            receipt = recorder.reconcile()
            summary = summarize(receipt["events"])
            self.assertTrue(receipt["complete"])
            self.assertEqual(summary["model_attempt_count"], 1)
            self.assertEqual(summary["tool_call_count"], 0)

    async def test_fake_provider_image_and_stale_generation_roundtrip_public_relay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            (server_root / "compiled-profile-mode").write_text("enabled")
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
            )

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            relay = Relay(ServerClient())
            caller = RecordedPublicMcpCaller(relay, recorder)

            try:
                observation = await caller.call_tool(
                    None, "observe-01", "interface_guarded_observe", {})
                content = observation["result"]["content"]
                images = [item for item in content if item.get("type") == "image"]
                self.assertEqual(len(images), 1, observation)
                image_data = base64.b64decode(images[0]["data"], validate=True)
                self.assertTrue(image_data.startswith(b"\x89PNG\r\n\x1a\n"))

                observed = json.loads(content[0]["text"])
                minted_call = await caller.call_tool(
                    None, "mint-01", "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": observed["source"]["sequence"],
                        "point": [8, 8],
                        "region_size": [12, 12],
                    })
                minted = json.loads(minted_call["result"]["content"][0]["text"])
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                payload["wait_for_result_ms"] = 10000
                generated_request = json.dumps(
                    payload, sort_keys=True, separators=(",", ":"),
                    allow_nan=False).encode("utf-8")
                image_path = root / "observed-image.bin"
                image_path.write_bytes(image_data)
                model_root = root / "model-call"

                def fake_model_call(call_root, prompt, image, contract, workspace):
                    self.assertEqual(prompt, "apply the highlighted synthetic target")
                    self.assertEqual(image.read_bytes(), image_data)
                    self.assertEqual(contract, "compiled")
                    self.assertEqual(workspace, root)
                    events_path = call_root / "model" / "events.jsonl"
                    events_path.parent.mkdir(parents=True)
                    rows = [
                        {"type": "thread.started", "thread_id": "synthetic-thread"},
                        {"type": "item.completed", "item": {
                            "type": "agent_message",
                            "text": generated_request.decode("utf-8")}},
                        {"type": "turn.completed", "usage": {
                            "input_tokens": 42, "output_tokens": 12}},
                    ]
                    events_path.write_bytes(b"".join(
                        json.dumps(row, separators=(",", ":")).encode() + b"\n"
                        for row in rows))
                    return {"usage": {"input_tokens": 42,
                                      "output_tokens": 12}}

                provider_request, fake_provider = build_model_provider_call(
                    model_call=fake_model_call, root=model_root,
                    prompt="apply the highlighted synthetic target",
                    image=image_path, contract="compiled", workspace=root)

                def prepare_arguments(generation):
                    # This callback runs after the provider terminal receipt but
                    # before standard Relay admission.
                    (server_root / "fake-process-generation").write_text(
                        "b" * 64, encoding="utf-8")
                    return parse_agent_message(generation["response_bytes"])

                composed = await caller.invoke_generation_to_tool(
                    "generation-stale-relay", provider_request, fake_provider,
                    "compiled-stale-relay", "interface_guarded_compiled",
                    prepare_arguments)
                generation = composed["generation"]
                self.assertEqual(generation["status"], "completed")
                self.assertEqual(generation["usage"]["input_tokens"], 42)
                self.assertEqual(generation["usage"]["output_tokens"], 12)
                self.assertEqual(
                    parse_agent_message(generation["response_bytes"]), payload)
                recorded_input = json.loads(next(
                    (recorder.root / ref["path"]).read_bytes()
                    for event in recorder.reconcile()["events"]
                    if event["kind"] == "model_attempt"
                    for ref in event["raw_refs"]
                    if ref["path"].endswith("generation-stale-relay.request.bin")))
                self.assertEqual(base64.b64decode(
                    recorded_input["image"]["data_base64"], validate=True), image_data)

                response = composed["tool_response"]
                result = json.loads(response["result"]["content"][0]["text"])
                self.assertEqual(response["status"], "returned")
                self.assertEqual(result["method_receipt"]["outcome"], "SAFE_YIELD")
                self.assertEqual(result["method_receipt"]["reason"],
                                 "execution_refused")
                self.assertEqual(result["method_receipt"]["completed_transitions"], 0)
                self.assertIsNone(result["task_success"])
                self.assertFalse(result["replay_allowed"])
                self.assertFalse(
                    (server_root / "synthetic-application-state.rgb").exists())

                initial_state = (
                    server_root / "synthetic-application-initial.rgb").read_bytes()
                task_success = Image.frombytes(
                    "RGB", (32, 32), initial_state, "raw", "BGRX"
                ).getpixel((1, 1)) == (255, 0, 0)
                self.assertFalse(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success, initial_state)
                receipt = recorder.reconcile()
                summary = summarize(receipt["events"])
                self.assertTrue(receipt["complete"])
                self.assertEqual(summary["model_attempt_count"], 1)
                self.assertEqual(summary["tool_call_count"], 3)
                self.assertEqual(summary["input_tokens"], 42)
                self.assertEqual(summary["output_tokens"], 12)
                self.assertFalse(summary["task_success"])
                self.assertEqual(
                    [event["response_status"] for event in receipt["events"]
                     if event["kind"] == "tool_call"],
                    ["matched", "matched", "matched"])
                generation_raw = next(
                    recorder.root / ref["path"]
                    for event in receipt["events"] if event["kind"] == "model_attempt"
                    for ref in event["raw_refs"]
                    if ref["path"].endswith("generation-stale-relay.request.bin"))
                generation_input = json.loads(generation_raw.read_bytes())
                self.assertEqual(base64.b64decode(
                    generation_input["image"]["data_base64"], validate=True),
                    image_data)
                self.assertEqual(
                    generation_input["image"]["sha256"],
                    hashlib.sha256(image_data).hexdigest())
                task_score = next(event for event in receipt["events"]
                                  if event["kind"] == "task_score")
                score_raw = recorder.root / task_score["raw_refs"][0]["path"]
                self.assertEqual(score_raw.read_bytes(), initial_state)
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("provider-public-relay-stale-generation", root)

    async def test_integrated_model_timeout_preserves_partial_events_and_skips_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image_path = root / "image.bin"
            image_path.write_bytes(b"image-bytes")
            model_root = root / "model-call"
            partial = b'{"type":"thread.started"}\n'

            def timed_out_model(call_root, *_args):
                events = call_root / "model" / "events.jsonl"
                events.parent.mkdir(parents=True)
                events.write_bytes(partial)
                raise TimeoutError("synthetic timeout")

            request, provider = build_model_provider_call(
                model_call=timed_out_model, root=model_root, prompt="p",
                image=image_path, contract="compiled", workspace=root)
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request):
                    raise AssertionError("timeout generation must not reach Relay")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            result = await caller.invoke_generation_to_tool(
                "generation-timeout", request, provider, "tool-after-timeout",
                "interface_guarded_compiled", parse_agent_message)
            self.assertFalse(result["tool_call_submitted"])
            self.assertEqual(result["generation"]["status"], "timeout")
            self.assertEqual(result["generation"]["usage"]["status"], "unavailable")
            receipt = recorder.reconcile()
            attempt = next(event for event in receipt["events"]
                           if event["kind"] == "model_attempt")
            self.assertEqual(attempt["status"], "timeout")
            response = next(ref for ref in attempt["raw_refs"]
                            if ref["path"].endswith("response.bin"))
            self.assertEqual((recorder.root / response["path"]).read_bytes(), partial)
            self.assertEqual(sum(event["kind"] == "tool_call"
                                 for event in receipt["events"]), 0)

    async def test_async_attempt_joins_generation_bound_public_compiled_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            (server_root / "compiled-profile-mode").parent.mkdir(parents=True)
            (server_root / "compiled-profile-mode").write_text("enabled")
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
            )
            try:
                observed = metadata(await server.call_tool(
                    "interface_guarded_observe", {}))
                minted = metadata(await server.call_tool(
                    "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": observed["source"]["sequence"],
                        "point": [8, 8],
                        "region_size": [12, 12],
                    }))
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                initial_application_state = (
                    server_root / "synthetic-application-initial.rgb").read_bytes()
                initial_image = Image.frombytes(
                    "RGB", (32, 32), initial_application_state, "raw", "BGRX")
                self.assertNotEqual(initial_image.getpixel((1, 1)), (255, 0, 0))
                payload["wait_for_result_ms"] = 10000
                generated_request = json.dumps(
                    payload, sort_keys=True, separators=(",", ":")).encode()

                async def provider_call():
                    return {
                        "status": "completed",
                        "usage": {"status": "reported", "input_tokens": 42,
                                  "output_tokens": 12},
                        "response_bytes": generated_request,
                    }

                generation = await recorder.invoke_async(
                    "generation-01", b"frozen provider request", provider_call)
                self.assertEqual(generation["response_bytes"], generated_request)
                generated_arguments = json.loads(generation["response_bytes"])

                async def compiled_tool_call():
                    response = await server.call_tool(
                        "interface_guarded_compiled", generated_arguments)
                    body = response.content[0].text.encode("utf-8")
                    return {"result": json.loads(body), "response_bytes": body}

                result = await recorder.invoke_tool_async(
                    "generation-01", "mcp-01", "interface_guarded_compiled",
                    generated_request, compiled_tool_call)
                application_state = (
                    server_root / "synthetic-application-state.rgb").read_bytes()
                image = Image.frombytes(
                    "RGB", (32, 32), application_state, "raw", "BGRX")
                task_success = image.getpixel((1, 1)) == (255, 0, 0)
                self.assertTrue(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success,
                    application_state)
                receipt = recorder.reconcile()
                summary = summarize(receipt["events"])

                self.assertTrue(receipt["complete"])
                self.assertEqual(result["method_receipt"]["outcome"],
                                 "TASK_SUCCEEDED")
                self.assertIsNone(result["task_success"])
                self.assertFalse(result["replay_allowed"])
                self.assertEqual(len(receipt["events"]), 3)
                self.assertEqual(receipt["events"][1]["model_attempt_id"],
                                 "generation-01")
                self.assertEqual(receipt["events"][1]["response_status"],
                                 "matched")
                self.assertEqual(receipt["events"][2]["kind"], "task_score")
                self.assertEqual(receipt["events"][2]["scorer_id"],
                                 "separate-fake-app-pixel-oracle-v1")
                self.assertTrue(receipt["events"][2]["task_success"])
                self.assertEqual(
                    Path(recorder.root, receipt["events"][2]["raw_refs"][0]["path"])
                    .read_bytes(), application_state)
                self.assertEqual(summary["model_attempt_count"], 1)
                self.assertEqual(summary["tool_call_count"], 1)
                self.assertEqual(summary["input_tokens"], 42)
                self.assertEqual(summary["output_tokens"], 12)
                self.assertTrue(summary["task_success"])
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("provider-mcp-success", root)

    async def test_provider_generated_request_is_refused_after_target_generation_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            (server_root / "compiled-profile-mode").parent.mkdir(parents=True)
            (server_root / "compiled-profile-mode").write_text("enabled")
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory,
            )
            try:
                observed = metadata(await server.call_tool(
                    "interface_guarded_observe", {}))
                minted = metadata(await server.call_tool(
                    "interface_guarded_mint", {
                        "alias": "field",
                        "source_sequence": observed["source"]["sequence"],
                        "point": [8, 8],
                        "region_size": [12, 12],
                    }))
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], minted["offset"])
                payload["wait_for_result_ms"] = 10000
                generated_request = json.dumps(
                    payload, sort_keys=True, separators=(",", ":")).encode()

                provider_started = asyncio.Event()
                provider_release = asyncio.Event()

                async def provider_call():
                    provider_started.set()
                    await provider_release.wait()
                    return {
                        "status": "completed",
                        "usage": {"status": "reported", "input_tokens": 42,
                                  "output_tokens": 12},
                        "response_bytes": generated_request,
                    }

                pending_generation = asyncio.create_task(recorder.invoke_async(
                    "generation-stale", b"frozen provider request", provider_call))
                await asyncio.wait_for(provider_started.wait(), timeout=2)
                (server_root / "fake-process-generation").write_text(
                    "b" * 64, encoding="utf-8")
                provider_release.set()
                generation = await asyncio.wait_for(pending_generation, timeout=2)
                generated_arguments = json.loads(generation["response_bytes"])

                async def compiled_tool_call():
                    response = await server.call_tool(
                        "interface_guarded_compiled", generated_arguments)
                    body = response.content[0].text.encode("utf-8")
                    return {"result": json.loads(body), "response_bytes": body}

                result = await recorder.invoke_tool_async(
                    "generation-stale", "mcp-stale", "interface_guarded_compiled",
                    generated_request, compiled_tool_call)
                method_receipt = result["method_receipt"]
                self.assertEqual(method_receipt["outcome"], "SAFE_YIELD")
                self.assertEqual(method_receipt["reason"], "execution_refused")
                self.assertEqual(method_receipt["completed_transitions"], 0)
                self.assertEqual(method_receipt["transitions"], [])
                self.assertFalse(
                    (server_root / "synthetic-application-state.rgb").exists())

                initial_state = (
                    server_root / "synthetic-application-initial.rgb").read_bytes()
                final_state = initial_state
                image = Image.frombytes(
                    "RGB", (32, 32), final_state, "raw", "BGRX")
                task_success = image.getpixel((1, 1)) == (255, 0, 0)
                self.assertFalse(task_success)
                recorder.record_task_score(
                    "separate-fake-app-pixel-oracle-v1", task_success, final_state)
                receipt = recorder.reconcile()
                summary = summarize(receipt["events"])

                self.assertTrue(receipt["complete"])
                self.assertIsNone(result["task_success"])
                self.assertFalse(result["replay_allowed"])
                self.assertEqual(len(receipt["events"]), 3)
                self.assertEqual(receipt["events"][1]["response_status"], "matched")
                self.assertGreater(receipt["events"][0]["ended_ns"],
                                   receipt["events"][0]["started_ns"])
                self.assertGreaterEqual(receipt["events"][1]["started_ns"],
                                        receipt["events"][0]["ended_ns"])
                self.assertEqual(receipt["events"][2]["kind"], "task_score")
                self.assertFalse(receipt["events"][2]["task_success"])
                self.assertEqual(
                    Path(recorder.root, receipt["events"][2]["raw_refs"][0]["path"])
                    .read_bytes(), final_state)
                self.assertEqual(summary["model_attempt_count"], 1)
                self.assertEqual(summary["tool_call_count"], 1)
                self.assertEqual(summary["input_tokens"], 42)
                self.assertEqual(summary["output_tokens"], 12)
                self.assertFalse(summary["task_success"])
            finally:
                await server.call_tool("interface_close", {})
                _preserve_fake_x_run("provider-mcp-stale-generation", root)


if __name__ == "__main__":
    unittest.main()
