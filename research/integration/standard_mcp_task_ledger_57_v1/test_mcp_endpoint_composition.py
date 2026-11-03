import asyncio
import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
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
                images = [item for item in observation["result"]["content"]
                          if item.get("type") == "image"]
                self.assertEqual(len(images), 1)
                image_bytes = base64.b64decode(images[0]["data"], validate=True)
                self.assertTrue(image_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
                image_path.write_bytes(image_bytes)
                with Image.open(image_path) as observed_image:
                    self.assertEqual(observed_image.format, "PNG")
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
                        self.image_bytes = Path(image_path).read_bytes()
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

                self.assertEqual(planner.image_bytes, image_bytes)
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
                images = [item for item in observation["result"]["content"]
                          if item.get("type") == "image"]
                self.assertEqual(len(images), 1)
                image_bytes = base64.b64decode(images[0]["data"], validate=True)
                self.assertTrue(image_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
                image_path.write_bytes(image_bytes)
                with Image.open(image_path) as observed_image:
                    self.assertEqual(observed_image.format, "PNG")
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
                        self.image_bytes = Path(image_path).read_bytes()
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

                planner = FakePlanner()
                model = AppServerPublicMcpModelCall(
                    planner, journal, workspace=workspace,
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
                self.assertEqual(planner.image_bytes, image_bytes)
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

    async def test_non_object_model_output_is_retained_without_gui_authority(self):
        """Reject incompatible structured output before public MCP dispatch."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            response_bytes = (
                b'{"type":"item.completed","item":'
                b'{"type":"agent_message","text":"[]"}}\n'
            )
            image_path = root / "image.bin"
            image_path.write_bytes(b"synthetic-observation")

            request = b'{"prompt":"return one object"}'

            async def provider():
                return {"status": "completed",
                        "usage": {"status": "reported",
                                  "input_tokens": 17, "output_tokens": 3},
                        "response_bytes": response_bytes}
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request):
                    raise AssertionError(
                        "schema-incompatible output must not reach public MCP")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            with self.assertRaisesRegex(ValueError, "JSON object"):
                await caller.invoke_generation_to_tool(
                    "generation-incompatible-schema", request, provider,
                    "tool-after-incompatible-schema",
                    "interface_guarded_compiled",
                    lambda generation: parse_agent_message(
                        generation["response_bytes"]))

            receipt = recorder.reconcile()
            attempt = next(event for event in receipt["events"]
                           if event["kind"] == "model_attempt")
            self.assertTrue(receipt["complete"])
            self.assertEqual(attempt["status"], "completed")
            self.assertEqual(attempt["usage"]["input_tokens"], 17)
            self.assertEqual(attempt["usage"]["output_tokens"], 3)
            response_ref = next(ref for ref in attempt["raw_refs"]
                                if ref["path"].endswith("response.bin"))
            self.assertEqual((recorder.root / response_ref["path"]).read_bytes(),
                             response_bytes)
            self.assertEqual(sum(event["kind"] == "tool_call"
                                 for event in receipt["events"]), 0)

    async def test_object_output_with_incompatible_mcp_shape_is_rejected_before_owner(self):
        """Route an object-shaped mismatch through real MCP argument validation."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(
                Relay(ServerClient(), tools={"interface_guarded_calc_compiled"}),
                recorder)
            response_bytes = (
                b'{"type":"item.completed","item":'
                b'{"type":"agent_message","text":"{}"}}\n'
            )

            async def provider():
                return {"status": "completed",
                        "usage": {"status": "reported",
                                  "input_tokens": 19, "output_tokens": 2},
                        "response_bytes": response_bytes}

            try:
                result = await caller.invoke_generation_to_tool(
                    "generation-object-schema-mismatch", b'{"prompt":"calc"}',
                    provider, "tool-object-schema-mismatch",
                    "interface_guarded_calc_compiled",
                    lambda generation: parse_agent_message(
                        generation["response_bytes"]))
                self.assertTrue(result["tool_call_submitted"])
                self.assertEqual(result["generation"]["status"], "completed")
                self.assertEqual(
                    result["tool_response"]["status"],
                    "returned", result["tool_response"])
                mcp_result = result["tool_response"]["result"]
                self.assertTrue(mcp_result["isError"], mcp_result)
                refusal = json.loads(mcp_result["content"][0]["text"])
                self.assertEqual(refusal["status"], "invalid_request", refusal)
                self.assertEqual(refusal["error"],
                                 "missing required tool arguments", refusal)
                self.assertEqual(refusal["missing_arguments"], [
                    "attempt_id", "bindings", "blank_reviewed", "profile_id",
                    "reviewed_artifact_sha256", "reviewed_sequence"], refusal)
                self.assertFalse(refusal["operation_invoked"], refusal)
                self.assertFalse(refusal["input_dispatched"], refusal)
                self.assertIsNone(refusal["task_success"], refusal)
                self.assertFalse(refusal["replay_allowed"], refusal)

                receipt = recorder.reconcile()
                attempt = next(event for event in receipt["events"]
                               if event["kind"] == "model_attempt")
                tool_call = next(event for event in receipt["events"]
                                 if event["kind"] == "tool_call")
                self.assertTrue(receipt["complete"])
                self.assertEqual(attempt["status"], "completed")
                self.assertEqual(attempt["usage"]["input_tokens"], 19)
                self.assertEqual(attempt["usage"]["output_tokens"], 2)
                raw_ref = next(ref for ref in attempt["raw_refs"]
                               if ref["path"].endswith("response.bin"))
                self.assertEqual((recorder.root / raw_ref["path"]).read_bytes(),
                                 response_bytes)
                self.assertEqual(tool_call["response_status"], "matched")
                self.assertEqual(sum(event["kind"] == "tool_call"
                                     for event in receipt["events"]), 1)
                self.assertFalse(list(server_root.glob("*/request.json")))
            finally:
                await server.call_tool("interface_close", {})

    async def test_object_output_with_invalid_registered_mcp_types_returns_refusal(self):
        """Type/constraint failures stop before the registered Calc handler."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server_root = root / "server"
            server_root.mkdir()
            recorder = ProviderAttemptRecorder(root / "ledger")
            server = create_server(
                {"app": 20}, server_root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)

            class ServerClient:
                async def call_tool(self, name, arguments):
                    return await server.call_tool(name, arguments)

            caller = RecordedPublicMcpCaller(
                Relay(ServerClient(), tools={"interface_guarded_calc_compiled"}),
                recorder)
            arguments = {
                "profile_id": 7,
                "bindings": {},
                "reviewed_sequence": 1,
                "reviewed_artifact_sha256": "not-a-sha256",
                "blank_reviewed": True,
                "attempt_id": "schema-type-refusal",
            }
            response_bytes = json.dumps({
                "type": "item.completed",
                "item": {"type": "agent_message",
                         "text": json.dumps(arguments)},
            }, separators=(",", ":")).encode("utf-8") + b"\n"

            async def provider():
                return {"status": "completed",
                        "usage": {"status": "reported",
                                  "input_tokens": 21, "output_tokens": 3},
                        "response_bytes": response_bytes}

            try:
                result = await caller.invoke_generation_to_tool(
                    "generation-invalid-registered-types", b'{"prompt":"calc"}',
                    provider, "tool-invalid-registered-types",
                    "interface_guarded_calc_compiled",
                    lambda generation: parse_agent_message(
                        generation["response_bytes"]))
                self.assertEqual(result["tool_response"]["status"], "returned")
                mcp_result = result["tool_response"]["result"]
                self.assertTrue(mcp_result["isError"], mcp_result)
                refusal = json.loads(mcp_result["content"][0]["text"])
                self.assertEqual(refusal["status"], "invalid_request", refusal)
                self.assertEqual(refusal["error"],
                                 "tool arguments failed schema validation", refusal)
                self.assertFalse(refusal["operation_invoked"], refusal)
                self.assertFalse(refusal["input_dispatched"], refusal)
                self.assertIsNone(refusal["task_success"], refusal)
                self.assertFalse(refusal["replay_allowed"], refusal)
                errors = refusal["validation_errors"]
                self.assertEqual({tuple(item["path"]) for item in errors}, {
                    ("profile_id",), ("reviewed_artifact_sha256",)})
                self.assertTrue(all("code" in item for item in errors))
                serialized_refusal = json.dumps(refusal)
                self.assertNotIn("not-a-sha256", serialized_refusal)
                self.assertNotIn('"input"', serialized_refusal)

                receipt = recorder.reconcile()
                attempt = next(event for event in receipt["events"]
                               if event["kind"] == "model_attempt")
                self.assertTrue(receipt["complete"])
                self.assertEqual(attempt["status"], "completed")
                self.assertEqual(attempt["usage"]["input_tokens"], 21)
                self.assertEqual(attempt["usage"]["output_tokens"], 3)
                raw_ref = next(ref for ref in attempt["raw_refs"]
                               if ref["path"].endswith("response.bin"))
                self.assertEqual((recorder.root / raw_ref["path"]).read_bytes(),
                                 response_bytes)
                self.assertFalse(list(server_root.glob("*/request.json")))
            finally:
                await server.call_tool("interface_close", {})

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

    async def test_cancelled_model_attempt_waits_for_worker_and_retains_cost_and_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image_path = root / "image.bin"
            image_path.write_bytes(b"image-bytes")
            model_root = root / "model-call"
            worker_started = threading.Event()
            allow_worker_finish = threading.Event()
            response_bytes = b'{"type":"turn.completed"}\n'

            def slow_model(call_root, *_args):
                worker_started.set()
                if not allow_worker_finish.wait(timeout=2):
                    raise TimeoutError("synthetic worker release deadline")
                events = call_root / "model" / "events.jsonl"
                events.parent.mkdir(parents=True)
                events.write_bytes(response_bytes)
                return {"usage": {"input_tokens": 23, "output_tokens": 5}}

            request, provider = build_model_provider_call(
                model_call=slow_model, root=model_root, prompt="p",
                image=image_path, contract="compiled", workspace=root)
            recorder = ProviderAttemptRecorder(root / "ledger")

            class RejectingRelay:
                next_id = 1

                async def request(self, _request):
                    raise AssertionError("cancelled generation must not reach Relay")

            caller = RecordedPublicMcpCaller(RejectingRelay(), recorder)
            pending = asyncio.create_task(caller.invoke_generation_to_tool(
                "generation-cancelled", request, provider,
                "tool-after-cancel", "interface_guarded_compiled",
                parse_agent_message))
            try:
                self.assertTrue(await asyncio.to_thread(
                    worker_started.wait, 2), "model worker did not start")
                pending.cancel()
                await asyncio.sleep(0)
                self.assertFalse(pending.done(),
                                 "first cancellation must retain worker custody")
                pending.cancel()
                await asyncio.sleep(0)
                self.assertFalse(pending.done(),
                                 "repeated cancellation must retain worker custody")
            finally:
                allow_worker_finish.set()

            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(pending, timeout=2)
            receipt = recorder.reconcile()
            self.assertTrue(receipt["complete"])
            attempt = next(event for event in receipt["events"]
                           if event["kind"] == "model_attempt")
            self.assertEqual(attempt["status"], "cancelled")
            self.assertEqual(attempt["usage"], {
                "status": "reported", "input_tokens": 23, "output_tokens": 5})
            response = next(ref for ref in attempt["raw_refs"]
                            if ref["path"].endswith("response.bin"))
            self.assertEqual((recorder.root / response["path"]).read_bytes(),
                             response_bytes)
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

    async def test_fake_app_server_generation_is_recorded_through_calc_profile_and_score(self):
        """Compose provider accounting, Calc public MCP, and an independent FODS score."""
        import xml.etree.ElementTree as ET
        import runtime.cli_v1.test_mcp_owned_process as calc_tests

        retained = os.environ.get("AGENT_INTERFACE_RETAIN_APP_SERVER_CALC_EVIDENCE")
        evidence_root = Path(retained).resolve() if retained else None
        if evidence_root is not None and evidence_root.exists():
            raise FileExistsError(evidence_root)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            image_path = root / "observation.png"
            Image.new("RGB", (8, 8), (220, 220, 220)).save(image_path)
            recorder = ProviderAttemptRecorder(root / "provider-ledger")
            provider_call_root = root / "provider-call"
            protocol_journal = root / "app-server" / "protocol.jsonl"
            protocol_journal.parent.mkdir()
            protocol_journal.write_text(
                '{"direction":"received","message":{"method":"thread/started"}}\n',
                encoding="utf-8")
            counts = {"tool": 0, "successful_generation": 0,
                      "provider_attempts": 0, "preflight_timeout_recorded": False,
                      "malformed_generation_recorded": False,
                      "stopped_generation_recorded": False,
                      "routed_profile_attempt_ids": set()}
            observed = {"artifact": None, "artifact_bytes": None,
                        "verification": None, "close": None,
                        "negative_profile_results": {}, "public_caller": None,
                        "compiled_result_candidates": [], "mint_receipts": [],
                        "provider_routed_compiled_results": []}
            test_case = self

            class ServerClient:
                def __init__(self, server):
                    self.server = server

                async def call_tool(self, name, arguments):
                    return await self.server.call_tool(name, arguments)

            original_create_server = calc_tests.create_server

            def create_recording_server(*args, **kwargs):
                server = original_create_server(*args, **kwargs)
                caller = RecordedPublicMcpCaller(
                    Relay(ServerClient(server), tools={
                        "interface_guarded_calc_compiled"}), recorder)
                observed["public_caller"] = caller

                class RecordingServer:
                    def __getattr__(self, name):
                        return getattr(server, name)

                    async def call_tool(self, name, arguments):
                        counts["tool"] += 1
                        call_id = f"calc-tool-{counts['tool']:04d}"
                        attempt_id = arguments.get("attempt_id")
                        if (name == "interface_guarded_calc_compiled" and
                                isinstance(attempt_id, str) and
                                attempt_id.startswith("calc-offline-") and
                                attempt_id not in counts["routed_profile_attempt_ids"]):
                            counts["routed_profile_attempt_ids"].add(attempt_id)
                            if (attempt_id == "calc-offline-e2e-01" and
                                    not counts["preflight_timeout_recorded"]):
                                counts["preflight_timeout_recorded"] = True
                                counts["provider_attempts"] += 1

                                class PreflightTimeout(TimeoutError):
                                    response_bytes = b'{"phase":"schema-preflight","partial":'

                                async def timed_out_preflight():
                                    raise PreflightTimeout(
                                        "synthetic schema preflight timeout")

                                with test_case.assertRaises(PreflightTimeout):
                                    await caller.invoke_provider(
                                        "calc-provider-preflight-00",
                                        b'{"task":"calc-save","phase":"schema-preflight"}',
                                        timed_out_preflight)

                            counts["successful_generation"] += 1
                            counts["provider_attempts"] += 1
                            provider_attempt_id = (
                                f"calc-provider-attempt-{counts['provider_attempts']:02d}")
                            provider_tool_call_id = (
                                f"calc-provider-tool-{counts['provider_attempts']:02d}")
                            answer = json.dumps(
                                arguments, sort_keys=True, separators=(",", ":"))
                            usage = {"last": {
                                "inputTokens": 42, "cachedInputTokens": 30,
                                "cacheWriteInputTokens": 2, "outputTokens": 12,
                                "reasoningOutputTokens": 3}}
                            thread_id = (
                                f"calc-fake-thread-{counts['successful_generation']:02d}")
                            turn_id = (
                                f"calc-fake-turn-{counts['successful_generation']:02d}")

                            class FakePlanner:
                                def begin_turn(self, prompt, *, output_schema,
                                               image_path):
                                    if (not prompt or output_schema != {"type": "object"} or
                                            not Path(image_path).is_file()):
                                        raise ValueError("invalid fake App Server request")
                                    return SimpleNamespace(thread_id=thread_id,
                                                           turn_id=turn_id)

                                def await_turn(self, handle, timeout):
                                    if timeout <= 0:
                                        raise ValueError("bounded fake turn required")
                                    events = [
                                        {"direction": "received", "message": {
                                            "method": "thread/tokenUsage/updated",
                                            "params": {"threadId": handle.thread_id,
                                                "turnId": handle.turn_id,
                                                "tokenUsage": usage}}},
                                        {"direction": "received", "message": {
                                            "method": "turn/completed",
                                            "params": {"threadId": handle.thread_id,
                                                "turn": {"id": handle.turn_id,
                                                    "status": "completed",
                                                    "items": [{"type": "agentMessage",
                                                        "text": answer}]}}}},
                                    ]
                                    with protocol_journal.open("a", encoding="utf-8") as stream:
                                        for event in events:
                                            stream.write(json.dumps(event,
                                                separators=(",", ":")) + "\n")
                                    return SimpleNamespace(answer_eligible=True,
                                        answer=json.loads(answer), status="completed",
                                        usage=usage)

                            model_call = AppServerPublicMcpModelCall(
                                FakePlanner(), protocol_journal, workspace=workspace,
                                contract="registered-calc-profile",
                                output_schema={"type": "object"},
                                model="fake-offline-model", effort="low")
                            request_bytes, provider_call = build_model_provider_call(
                                model_call=model_call.call,
                                root=provider_call_root / provider_attempt_id,
                                prompt="Execute the supplied registered Calc task request.",
                                image=image_path, contract="registered-calc-profile",
                                workspace=workspace)

                            def prepare_arguments(generation):
                                backend = generation["backend_result"]
                                return parse_app_server_tool_request(
                                    generation["response_bytes"],
                                    thread_id=backend["thread_id"],
                                    turn_id=backend["turn_id"])

                            joined = await caller.invoke_generation_to_tool(
                                provider_attempt_id, request_bytes,
                                provider_call, provider_tool_call_id, name,
                                prepare_arguments)
                            if not joined["tool_call_submitted"]:
                                raise AssertionError(joined)
                            response_text = joined["tool_response"]["result"][
                                "content"][0]["text"]
                            if name == "interface_guarded_calc_compiled":
                                observed["provider_routed_compiled_results"].append({
                                    "attempt_id": arguments.get("attempt_id"),
                                    "bindings": arguments.get("bindings"),
                                    "prepared_call_id": arguments.get(
                                        "prepared_call_id"),
                                    "reviewed_sequence": arguments.get(
                                        "reviewed_sequence"),
                                    "body": json.loads(response_text)})
                            if attempt_id != "calc-offline-e2e-01":
                                observed["negative_profile_results"][attempt_id] = (
                                    json.loads(response_text))
                            return SimpleNamespace(content=[SimpleNamespace(
                                text=response_text)])

                        request = {"id": counts["tool"], "tool": name,
                                   "arguments": arguments}
                        request_bytes = json.dumps(request, sort_keys=True,
                            separators=(",", ":")).encode("utf-8")

                        async def invoke_tool():
                            result = await server.call_tool(name, arguments)
                            result_bytes = json.dumps(result.model_dump(mode="json"),
                                sort_keys=True, separators=(",", ":")).encode("utf-8")
                            return {"result": json.loads(result_bytes),
                                    "response_bytes": result_bytes}

                        result = await recorder.invoke_tool_async(
                            None, call_id, name, request_bytes, invoke_tool)
                        body = metadata(SimpleNamespace(content=[SimpleNamespace(
                            text=result["content"][0]["text"])]))
                        if name == "interface_guarded_calc_compiled":
                            observed["compiled_result_candidates"].append({
                                "attempt_id": arguments.get("attempt_id"),
                                "reviewed_sequence": arguments.get("reviewed_sequence"),
                                "bindings": arguments.get("bindings"),
                                "body": body})
                        if name == "interface_guarded_mint":
                            observed["mint_receipts"].append({
                                "requested_alias": arguments.get("alias"),
                                "requested_source_sequence": arguments.get(
                                    "source_sequence"),
                                "requested_point": arguments.get("point"),
                                "body": body})
                        if name == "interface_guarded_calc_prepare" and body.get(
                                "status") == "prepared":
                            observed["artifact"] = Path(body["artifact_path"])
                        if name == "interface_verify_task" and body.get(
                                "status") == "verified":
                            observed["artifact_bytes"] = observed["artifact"].read_bytes()
                            observed["verification"] = body
                        if name == "interface_close":
                            observed["close"] = body
                        return SimpleNamespace(content=[SimpleNamespace(
                            text=result["content"][0]["text"])])

                return RecordingServer()

            runtime_evidence = (evidence_root / "raw-runtime"
                                if evidence_root is not None else None)
            env = {}
            if runtime_evidence is not None:
                env["AGENT_INTERFACE_RETAIN_CALC_PROFILE_EVIDENCE"] = str(
                    runtime_evidence)
            with patch.dict(os.environ, env), patch.object(
                    calc_tests, "create_server", create_recording_server):
                case = calc_tests.OwnedProcessMCPTests(
                    "test_registered_calc_profile_runs_through_owned_mcp_and_releases")
                await case.test_registered_calc_profile_runs_through_owned_mcp_and_releases()
                negative_case = calc_tests.OwnedProcessMCPTests(
                    "test_registered_calc_profile_stops_on_wrong_unknown_no_match_or_ambiguous_ocr")
                await negative_case.test_registered_calc_profile_stops_on_wrong_unknown_no_match_or_ambiguous_ocr()

            # A malformed terminal provider result is an attempted generation,
            # but it must not be parsed into or dispatched as an MCP tool call.
            counts["provider_attempts"] += 1
            malformed_attempt_id = (
                f"calc-provider-attempt-{counts['provider_attempts']:02d}")
            malformed_raw = b'{"generation":"truncated'

            async def malformed_provider_result():
                return {
                    "status": "malformed",
                    "usage": {"status": "unavailable",
                              "input_tokens": None, "output_tokens": None},
                    "response_bytes": malformed_raw,
                    "error_type": "structured_response_malformed",
                }

            def malformed_must_not_be_parsed(_generation):
                raise AssertionError("malformed generation reached MCP parser")

            malformed_tool_calls_before = counts["tool"]
            malformed = await observed["public_caller"].invoke_generation_to_tool(
                malformed_attempt_id,
                b'{"task":"calc-save","phase":"malformed-generation"}',
                malformed_provider_result, "calc-provider-malformed-tool-06",
                "interface_guarded_calc_compiled",
                malformed_must_not_be_parsed)
            counts["malformed_generation_recorded"] = True
            self.assertFalse(malformed["tool_call_submitted"], malformed)
            self.assertEqual(malformed["generation"]["status"], "malformed",
                             malformed)
            self.assertEqual(counts["tool"], malformed_tool_calls_before)

            counts["provider_attempts"] += 1
            stopped_attempt_id = (
                f"calc-provider-attempt-{counts['provider_attempts']:02d}")

            async def stopped_provider_result():
                return {
                    "status": "cancelled",
                    "usage": {"status": "unavailable",
                              "input_tokens": None, "output_tokens": None},
                    "response_bytes": b'{"turn_status":"cancelled"}',
                }

            stopped_tool_calls_before = counts["tool"]
            stopped = await observed["public_caller"].invoke_generation_to_tool(
                stopped_attempt_id,
                b'{"task":"calc-save","phase":"cancelled-generation"}',
                stopped_provider_result, "calc-provider-cancelled-tool-07",
                "interface_guarded_calc_compiled",
                malformed_must_not_be_parsed)
            counts["stopped_generation_recorded"] = True
            self.assertFalse(stopped["tool_call_submitted"], stopped)
            self.assertEqual(stopped["generation"]["status"], "cancelled", stopped)
            self.assertEqual(counts["tool"], stopped_tool_calls_before)

            self.assertEqual(counts["successful_generation"], 5)
            self.assertEqual(counts["provider_attempts"], 8)
            self.assertTrue(counts["malformed_generation_recorded"])
            self.assertTrue(counts["stopped_generation_recorded"])
            self.assertGreater(counts["tool"], 1)
            self.assertEqual(set(observed["negative_profile_results"]), {
                "calc-offline-wrong-after-input",
                "calc-offline-unknown-after-input",
                "calc-offline-no-match-after-input",
                "calc-offline-ambiguous-after-input"})
            for attempt_id, expected_reason in (
                    ("calc-offline-wrong-after-input", "effect_failed"),
                    ("calc-offline-unknown-after-input", "effect_unavailable"),
                    ("calc-offline-no-match-after-input", "effect_unavailable"),
                    ("calc-offline-ambiguous-after-input", "effect_unavailable")):
                negative = observed["negative_profile_results"][attempt_id]
                self.assertEqual(negative["method_receipt"]["outcome"],
                                 "SAFE_YIELD", negative)
                self.assertEqual(negative["method_receipt"]["reason"],
                                 expected_reason, negative)
                self.assertEqual(negative["method_receipt"]["completed_transitions"],
                                 1, negative)
                self.assertTrue(all(row["release_verified"] is True for row in
                                    negative["method_receipt"]["transitions"]), negative)
                self.assertIsNone(negative["task_success"], negative)
                self.assertFalse(negative["replay_allowed"], negative)
            self.assertTrue(observed["verification"]["task_success"])
            self.assertTrue(observed["close"]["release_confirmed"])
            provider_primary = next(candidate["body"] for candidate in
                observed["compiled_result_candidates"]
                if candidate["attempt_id"] == "calc-offline-e2e-01")
            self.assertEqual(provider_primary["status"], "invalid_request",
                             provider_primary)
            self.assertEqual(provider_primary["error"],
                "CALC_BINDING_NOT_MINTED_FOR_REVIEWED_SOURCE", provider_primary)
            self.assertFalse(provider_primary["operation_invoked"], provider_primary)
            self.assertFalse(provider_primary["input_dispatched"], provider_primary)
            self.assertIsNone(provider_primary["task_success"], provider_primary)
            self.assertFalse(provider_primary["replay_allowed"], provider_primary)
            routed_primary = next(candidate for candidate in
                observed["provider_routed_compiled_results"]
                if candidate["attempt_id"] == "calc-offline-e2e-01")
            routed_receipt = routed_primary["body"]["method_receipt"]
            self.assertEqual(routed_receipt["outcome"], "SAFE_YIELD",
                             routed_primary)
            self.assertEqual(routed_receipt["reason"], "effect_unavailable",
                             routed_primary)
            self.assertEqual(routed_receipt["completed_transitions"], 2,
                             routed_primary)
            self.assertTrue(all(row["release_verified"] is True for row in
                                routed_receipt["transitions"]), routed_primary)
            self.assertIsNone(routed_primary["body"]["task_success"],
                              routed_primary)
            self.assertFalse(routed_primary["body"]["replay_allowed"],
                             routed_primary)
            artifact_bytes = observed["artifact_bytes"]
            self.assertIsInstance(artifact_bytes, bytes)
            verified_effect = observed["verification"]["task_effect"]
            save_controller = verified_effect["save_controller"]
            provider_method_receipt_sha256 = hashlib.sha256(json.dumps(
                routed_receipt, sort_keys=True, separators=(",", ":"),
                allow_nan=False).encode("utf-8")).hexdigest()
            self.assertTrue(observed["verification"]["task_success"])
            self.assertEqual(verified_effect["attempt_id"],
                             routed_primary["attempt_id"])
            self.assertEqual(save_controller["attempt_id"],
                             routed_primary["attempt_id"])
            self.assertEqual(save_controller["call_id"],
                             routed_primary["prepared_call_id"])
            self.assertEqual(save_controller["method_receipt_sha256"],
                             provider_method_receipt_sha256)
            self.assertEqual(verified_effect["profile_id"], "calc-ocr-save-v1")
            self.assertEqual(verified_effect["artifact_sha256"],
                             hashlib.sha256(artifact_bytes).hexdigest())
            scoped_mints = [row for row in observed["mint_receipts"]
                if row["body"].get("session", {}).get("compiled_scope") ==
                routed_receipt["session_scope"]]
            mint_offsets = {row["requested_alias"]: row["body"].get("offset")
                for row in scoped_mints if row["body"].get("status") == "minted"}
            self.assertEqual(mint_offsets, {
                binding["alias"]: binding["offset"] for binding in
                routed_primary["bindings"].values()})
            self.assertEqual(len(scoped_mints), 2)
            root_xml = ET.fromstring(artifact_bytes)
            office_ns = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
            scored_values = [cell.attrib.get(f"{{{office_ns}}}value")
                for cell in root_xml.iter()
                if cell.tag.endswith("table-cell") and
                cell.attrib.get(f"{{{office_ns}}}value") is not None]
            expected_values = ["24680", "13579"]
            self.assertEqual(scored_values, expected_values)
            recorder.record_task_score(
                "stdlib-fods-cell-values-v1", scored_values == expected_values,
                artifact_bytes)
            receipt = recorder.reconcile()
            summary = summarize(receipt["events"])
            malformed_event = next(event for event in receipt["events"]
                if event["kind"] == "model_attempt" and
                event["attempt_id"] == malformed_attempt_id)
            stopped_event = next(event for event in receipt["events"]
                if event["kind"] == "model_attempt" and
                event["attempt_id"] == stopped_attempt_id)
            self.assertTrue(receipt["complete"])
            self.assertEqual(summary["model_attempt_count"], 8)
            self.assertEqual(malformed_event["status"], "malformed")
            self.assertEqual(malformed_event["usage"]["status"], "unavailable")
            self.assertEqual(malformed_event["response_status"], "raw_retained")
            self.assertEqual(stopped_event["status"], "cancelled")
            self.assertEqual(stopped_event["usage"]["status"], "unavailable")
            self.assertEqual(stopped_event["response_status"], "raw_retained")
            self.assertEqual(summary["tool_call_count"], counts["tool"])
            self.assertEqual(summary["usage_status"], "incomplete")
            self.assertIsNone(summary["input_tokens"])
            self.assertIsNone(summary["output_tokens"])
            self.assertEqual(summary["detailed_usage_status"], "incomplete")
            self.assertIsNone(summary["cached_input_tokens"])
            self.assertIsNone(summary["cache_write_input_tokens"])
            self.assertIsNone(summary["reasoning_output_tokens"])
            self.assertIsNone(summary["image_input_tokens"])
            self.assertTrue(summary["task_success"])

            if evidence_root is not None:
                if not evidence_root.is_dir() or {
                        item.name for item in evidence_root.iterdir()} != {"raw-runtime"}:
                    raise FileExistsError(evidence_root)
                shutil.copytree(recorder.root, evidence_root / "provider-ledger")
                shutil.copytree(provider_call_root, evidence_root / "provider-call")
                shutil.copy2(protocol_journal, evidence_root / "app-server-protocol.jsonl")
                (evidence_root / "joined-ledger-summary.json").write_text(
                    json.dumps(summary, sort_keys=True, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")
                (evidence_root / "boundary-results.json").write_text(
                    json.dumps({
                        "schema": "agent-interface/fake-appserver-calc-boundary-v1",
                        "provider": "synthetic_fake_planner_echoes_supplied_arguments",
                        "model_generations": counts["successful_generation"],
                        "provider_attempts": counts["provider_attempts"],
                        "malformed_generation_recorded":
                            counts["malformed_generation_recorded"],
                        "stopped_generation_recorded":
                            counts["stopped_generation_recorded"],
                        "malformed_model_attempt": {
                            "attempt_id": malformed_event["attempt_id"],
                            "status": malformed_event["status"],
                            "usage_status": malformed_event["usage"]["status"],
                            "response_status": malformed_event["response_status"],
                        },
                        "stopped_model_attempt": {
                            "attempt_id": stopped_event["attempt_id"],
                            "status": stopped_event["status"],
                            "usage_status": stopped_event["usage"]["status"],
                            "response_status": stopped_event["response_status"],
                        },
                        "public_mcp_tool_calls": counts["tool"],
                        "model_attempts": [
                            {"attempt_id": row["attempt_id"],
                             "status": row["status"],
                             "usage_status": row["usage"]["status"]}
                            for row in receipt["events"]
                            if row["kind"] == "model_attempt"],
                        "negative_profile_results": {
                            attempt_id: {
                                "outcome": result["method_receipt"]["outcome"],
                                "reason": result["method_receipt"]["reason"],
                                "completed_transitions": result["method_receipt"][
                                    "completed_transitions"],
                                "released_transitions": [
                                    row["release_verified"] for row in
                                    result["method_receipt"]["transitions"]],
                                "task_success": result["task_success"],
                                "replay_allowed": result["replay_allowed"]}
                            for attempt_id, result in
                            observed["negative_profile_results"].items()},
                        "separate_direct_task_effect": observed["verification"],
                        "separate_direct_owner_close": observed["close"],
                        "independent_stdlib_fods_values": scored_values,
                        "independent_fods_value_match": scored_values == expected_values,
                        "verified_task_effect_success":
                            observed["verification"]["task_effect"]["task_success"],
                        "provider_compiled_call_candidates": [
                            {"attempt_id": candidate["attempt_id"],
                             "reviewed_sequence": candidate["reviewed_sequence"],
                             "bindings": candidate["bindings"],
                             "status": candidate["body"].get("status"),
                             "task_success": candidate["body"].get("task_success"),
                             "error": candidate["body"].get("error"),
                             "detail": candidate["body"].get("detail"),
                             "handoff_reason": candidate["body"].get(
                                 "method_receipt", {}).get("reason"),
                             "keys": sorted(candidate["body"])}
                            for candidate in observed["compiled_result_candidates"]],
                        "provider_routed_compiled_call_results": [
                            {"attempt_id": candidate["attempt_id"],
                             "bindings": candidate["bindings"],
                             "outcome": candidate["body"].get(
                                 "method_receipt", {}).get("outcome"),
                             "reason": candidate["body"].get(
                                 "method_receipt", {}).get("reason"),
                             "completed_transitions": candidate["body"].get(
                                 "method_receipt", {}).get("completed_transitions"),
                             "release_verified": [row.get("release_verified")
                                 for row in candidate["body"].get(
                                     "method_receipt", {}).get("transitions", [])],
                             "task_success": candidate["body"].get("task_success"),
                             "replay_allowed": candidate["body"].get(
                                 "replay_allowed")}
                            for candidate in
                            observed["provider_routed_compiled_results"]],
                        "provider_task_effect_join": {
                            "status": observed["verification"]["status"],
                            "task_success": observed["verification"]["task_success"],
                            "attempt_id": routed_primary["attempt_id"],
                            "prepared_call_id": routed_primary["prepared_call_id"],
                            "save_controller_call_id": save_controller["call_id"],
                            "provider_method_receipt_sha256":
                                provider_method_receipt_sha256,
                            "save_controller_method_receipt_sha256":
                                save_controller["method_receipt_sha256"],
                            "compiled_scope": routed_receipt["session_scope"],
                            "minted_alias_offsets": mint_offsets,
                            "verified_artifact_sha256":
                                verified_effect["artifact_sha256"],
                            "replay_allowed": verified_effect["replay_allowed"]},
                        "public_mint_receipts": observed["mint_receipts"],
                        "limits": ["FakeX_only", "no_live_provider", "no_live_Calc",
                                   "no_efficiency_comparison"]},
                        sort_keys=True, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")

    async def test_calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases(self):
        """Hold a model turn across a title/source change, then recover once."""
        import xml.etree.ElementTree as ET
        import runtime.cli_v1.test_mcp_owned_process as calc_tests
        from runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 import plan as calc_plan
        from runtime.guarded_x11_v1.process_identity import (
            process_generation_from_identity,process_incarnation_from_identity)

        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            server_root=root/'server'; server_root.mkdir()
            task_values={'A1':'24680','A2':'13579'}
            task_plan=calc_plan()
            (server_root/'calc-task-values.json').write_text(
                json.dumps(task_values),encoding='utf-8')
            (server_root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
            (server_root/'fake-target-exit-receipt').write_text('enabled',encoding='utf-8')
            (server_root/'fake-calc-save-writes-artifact').write_text(
                'enabled',encoding='utf-8')
            (server_root/'fake-calc-record-point-resolution').write_text(
                'enabled',encoding='utf-8')
            workspace=root/'workspace'; workspace.mkdir()
            journal=root/'app-server'/'protocol.jsonl'; journal.parent.mkdir()
            journal.write_bytes(b'{"direction":"received","message":{"method":"thread/started"}}\n')
            recorder=ProviderAttemptRecorder(root/'provider-ledger')
            server=create_server({'app':20},server_root,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,
                guarded_window_lifecycle=True,guarded_owned_process=True,
                _guarded_owner_factory=_fake_owner_factory)

            class ServerClient:
                async def call_tool(self,name,arguments):
                    return await server.call_tool(name,arguments)

            caller=RecordedPublicMcpCaller(Relay(ServerClient(),tools={
                'interface_guarded_observe','interface_guarded_mint',
                'interface_guarded_calc_prepare','interface_guarded_calc_compiled',
                'interface_close','interface_verify_task'}),recorder)
            phase_ns={}
            provider_waiting=threading.Event()
            release_provider=threading.Event()
            class FakePlanner:
                def __init__(self):
                    self.turn_index=0
                    self.payloads=[]
                def begin_turn(self,prompt,*,output_schema,image_path):
                    index=self.turn_index; self.turn_index+=1
                    return SimpleNamespace(thread_id=f'calc-thread-{index+1}',
                        turn_id=f'calc-turn-{index+1}',index=index)
                def await_turn(self,handle,timeout):
                    if handle.index==0:
                        self.wait_started_ns=time.monotonic_ns()
                        provider_waiting.set()
                        if not release_provider.wait(timeout=5):
                            raise TimeoutError('synthetic provider wait did not resume')
                    usage={'last':{'inputTokens':40+10*handle.index,
                        'outputTokens':9+2*handle.index,
                        'cachedInputTokens':10,'cacheWriteInputTokens':1,
                        'reasoningOutputTokens':0}}
                    text=json.dumps(self.payloads[handle.index],separators=(',',':'))
                    rows=(
                        {'direction':'received','observed_ns':10+handle.index*10,
                         'message':{'method':'thread/tokenUsage/updated','params':{
                            'threadId':handle.thread_id,'turnId':handle.turn_id,
                            'tokenUsage':usage}}},
                        {'direction':'received','observed_ns':11+handle.index*10,
                         'message':{'method':'turn/completed','params':{
                            'threadId':handle.thread_id,'turn':{'id':handle.turn_id,
                            'status':'completed','items':[{'type':'agentMessage',
                            'text':text}]}}}})
                    with journal.open('ab') as stream:
                        for row in rows:
                            stream.write(json.dumps(row,separators=(',',':')).encode()+b'\n')
                    return SimpleNamespace(status='completed',answer_eligible=True,
                        answer=self.payloads[handle.index],usage=usage)

            planner=FakePlanner()
            model=AppServerPublicMcpModelCall(planner,journal,workspace=workspace,
                contract='registered-calc-profile',output_schema={'type':'object'},
                model='fake-wait-model',effort='low')

            async def observe_and_save_image(call_id):
                response=await caller.call_tool(None,call_id,
                    'interface_guarded_observe',{})
                body=json.loads(response['result']['content'][0]['text'])
                images=[row for row in response['result']['content']
                        if row.get('type')=='image']
                self.assertEqual(len(images),1)
                image_bytes=base64.b64decode(images[0]['data'],validate=True)
                image_path=root/f'{call_id}.png'; image_path.write_bytes(image_bytes)
                return body,image_path

            async def mint(source, suffix):
                entry_response=await caller.call_tool(None,f'{suffix}-entry',
                    'interface_guarded_mint',{'alias':f'entry_{suffix}',
                    'source_sequence':source['sequence'],'point':[16,31],
                    'region_size':[24,16],'freshness_ms':5000})
                save_response=await caller.call_tool(None,f'{suffix}-save',
                    'interface_guarded_mint',{'alias':f'save_{suffix}',
                    'source_sequence':source['sequence'],'point':[200,205],
                    'region_size':[16,12],'freshness_ms':5000})
                entry=json.loads(entry_response['result']['content'][0]['text'])
                save=json.loads(save_response['result']['content'][0]['text'])
                self.assertEqual(entry['status'],'minted',entry)
                self.assertEqual(save['status'],'minted',save)
                return {'entry':{'alias':f'entry_{suffix}','offset':entry['offset']},
                        'save':{'alias':f'save_{suffix}','offset':save['offset']}}

            def payload(source,bindings,attempt_id,prepared_call_id=None):
                row={'profile_id':'calc-ocr-save-v1','bindings':bindings,
                    'reviewed_sequence':source['sequence'],
                    'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                    'blank_reviewed':True,'attempt_id':attempt_id,
                    'wait_for_result_ms':10000}
                if prepared_call_id is not None:
                    row['prepared_call_id']=prepared_call_id
                return row

            def parse_generation(generation):
                backend=generation['backend_result']
                return parse_app_server_tool_request(generation['response_bytes'],
                    thread_id=backend['thread_id'],turn_id=backend['turn_id'])

            def parse_tool_arguments(generation, expected_method):
                request=parse_generation(generation)
                if request.get('method') != expected_method:
                    raise ValueError('provider selected an unexpected public MCP method')
                arguments=request.get('arguments')
                if not isinstance(arguments,dict):
                    raise ValueError('provider tool arguments must be an object')
                return arguments

            try:
                phase_started=time.monotonic_ns()
                old,old_image=await observe_and_save_image('observe-old')
                phase_ns['initial_observe']=time.monotonic_ns()-phase_started
                old_source=old['source']
                phase_started=time.monotonic_ns()
                old_bindings=await mint(old_source,'old')
                phase_ns['initial_mint']=time.monotonic_ns()-phase_started
                planner.payloads.append(payload(old_source,old_bindings,
                    'calc-wait-attempt-01'))
                request1,provider1=build_model_provider_call(model_call=model.call,
                    root=root/'provider-call'/'attempt-01',
                    prompt='Use this reviewed Calc source to perform the task.',
                    image=old_image,contract='registered-calc-profile',workspace=workspace)
                first_task=asyncio.create_task(caller.invoke_generation_to_tool(
                    'calc-wait-attempt-01',request1,provider1,'calc-wait-call-01',
                    'interface_guarded_calc_compiled',parse_generation))
                self.assertTrue(await asyncio.to_thread(provider_waiting.wait,5))
                provider_wait_started_ns=planner.wait_started_ns

                # The model has the old source while the application metadata changes.
                stale_generation_started_ns=time.monotonic_ns()
                (server_root/'fake-window-metadata-changed-calc').write_text(
                    'changed-during-provider-wait',encoding='utf-8')
                changed,changed_image=await observe_and_save_image(
                    'observe-during-provider-wait')
                changed_source=changed['source']
                self.assertGreater(changed_source['sequence'],
                    old_source['sequence'])
                release_provider.set()
                phase_ns['provider_wait_including_stale_observation']= (
                    time.monotonic_ns()-provider_wait_started_ns)
                first=await first_task
                phase_ns['stale_generation_to_refusal']=time.monotonic_ns()-stale_generation_started_ns
                self.assertTrue(first['tool_call_submitted'],first)
                first_body=json.loads(first['tool_response']['result']['content'][0]['text'])
                self.assertEqual(first['generation']['status'],'completed')
                self.assertIn('status',first_body,first_body)
                self.assertEqual(first_body['status'],'invalid_request',first_body)
                self.assertEqual(first_body['error'],'CALC_REVIEW_SOURCE_STALE',first_body)
                self.assertFalse(first_body['operation_invoked'],first_body)
                self.assertFalse(first_body['input_dispatched'],first_body)
                self.assertIsNone(first_body['release_confirmed'],first_body)
                self.assertIsNone(first_body['task_success'],first_body)
                self.assertFalse(first_body['replay_allowed'],first_body)
                self.assertFalse(list(server_root.rglob('calc-fake-state.json')))

                phase_started=time.monotonic_ns()
                fresh,fresh_image=await observe_and_save_image('observe-after-wait')
                phase_ns['fresh_observe']=time.monotonic_ns()-phase_started
                self.assertGreater(fresh['source']['sequence'],
                    changed_source['sequence'])
                phase_started=time.monotonic_ns()
                new_bindings=await mint(fresh['source'],'fresh')
                phase_ns['fresh_mint']=time.monotonic_ns()-phase_started
                self.assertEqual(new_bindings['entry']['offset'],[12,8],
                    new_bindings)

                # The provider response, not the test harness call site, now
                # carries the symbolic plan into the parent-owned preparation.
                task_attempt_id='calc-wait-attempt-02'
                prepare_tool={'method':'interface_guarded_calc_prepare',
                    'arguments':{'attempt_id':task_attempt_id,
                        'task_values':task_values,'task_plan':task_plan}}
                planner.payloads.append(prepare_tool)
                request2,provider2=build_model_provider_call(model_call=model.call,
                    root=root/'provider-call'/'attempt-02-prepare',
                    prompt='From the fresh Calc image, propose the bounded task plan and prepare the task.',
                    image=fresh_image,contract='registered-calc-profile',workspace=workspace)
                phase_started=time.monotonic_ns()
                prepare_generation=await caller.invoke_generation_to_tool(
                    'calc-wait-attempt-02',request2,provider2,
                    'calc-wait-call-02-prepare','interface_guarded_calc_prepare',
                    lambda generation: parse_tool_arguments(
                        generation,'interface_guarded_calc_prepare'))
                phase_ns['provider_authored_prepare']=time.monotonic_ns()-phase_started
                self.assertEqual(prepare_generation['generation']['status'],
                                 'completed')
                self.assertTrue(prepare_generation['tool_call_submitted'])
                prepared=json.loads(prepare_generation['tool_response'][
                    'result']['content'][0]['text'])
                self.assertEqual(prepared['status'],'prepared',prepared)
                self.assertEqual(prepared['task_values'],task_values,prepared)
                self.assertEqual(len(prepared['task_plan_sha256']),64,prepared)
                retained_request=parse_generation(
                    prepare_generation['generation'])
                self.assertEqual(retained_request['arguments']['task_plan'],task_plan)
                self.assertEqual(retained_request['arguments']['task_values'],task_values)
                self.assertEqual(retained_request['arguments']['attempt_id'],
                                 task_attempt_id)

                planner.payloads.append({'method':'interface_guarded_calc_compiled',
                    'arguments':payload(fresh['source'],new_bindings,
                        task_attempt_id,prepared['call_id'])})
                request2,provider2=build_model_provider_call(model_call=model.call,
                    root=root/'provider-call'/'attempt-03-execute',
                    prompt='Use the retained prepared plan and these freshly minted bindings to execute once.',
                    image=fresh_image,contract='registered-calc-profile',workspace=workspace)
                phase_started=time.monotonic_ns()
                second=await caller.invoke_generation_to_tool('calc-wait-attempt-03',
                    request2,provider2,'calc-wait-call-03-execute',
                    'interface_guarded_calc_compiled',lambda generation:
                        parse_tool_arguments(generation,
                            'interface_guarded_calc_compiled'))
                phase_ns['fresh_provider_to_compiled_result']=time.monotonic_ns()-phase_started
                result=json.loads(second['tool_response']['result']['content'][0]['text'])
                self.assertEqual(second['generation']['status'],'completed')
                self.assertIn('method_receipt',result)
                self.assertIsNone(result['task_success'],result)
                self.assertEqual(result['method_receipt']['outcome'],'SAFE_YIELD',result)
                self.assertEqual(result['method_receipt']['reason'],'effect_unavailable',result)
                self.assertEqual(result['method_receipt']['completed_transitions'],2,result)
                self.assertEqual(result['method_receipt']['task_plan_sha256'],
                                 prepared['task_plan_sha256'],result)
                self.assertEqual(result['task_artifact_admission']['expected_values'],
                                 task_values,result)
                self.assertTrue(all(row['release_verified'] is True for row in
                    result['method_receipt']['transitions']),result)
                self.assertFalse(result['replay_allowed'],result)
                phase_ns['compiled_graph_runtime']= (
                    result['method_receipt']['ended_ns']
                    - result['method_receipt']['started_ns'])

                phase_started=time.monotonic_ns()
                close_response=await caller.call_tool(None,'close-after-repair',
                    'interface_close',{})
                phase_ns['neutral_close']=time.monotonic_ns()-phase_started
                closed=json.loads(close_response['result']['content'][0]['text'])
                self.assertTrue(closed['verified'],closed)
                self.assertTrue(closed['release_confirmed'],closed)
                artifact_path=Path(prepared['artifact_path'])
                self.assertTrue(artifact_path.is_file(),artifact_path)
                fake_state=json.loads(next(server_root.rglob(
                    'calc-fake-state.json')).read_text(encoding='utf-8'))
                self.assertTrue(fake_state['save_requested'],fake_state)
                self.assertEqual(fake_state['completed_entries'],
                                 [task_values['A1'],task_values['A2']],fake_state)
                self.assertTrue(fake_state['artifact_written_on_save'],fake_state)
                phase_started=time.monotonic_ns()
                verified_response=await caller.call_tool(None,'verify-after-repair',
                    'interface_verify_task',{'call_id':result['call_id']})
                phase_ns['post_close_independent_score']=time.monotonic_ns()-phase_started
                verified=json.loads(verified_response['result']['content'][0]['text'])
                self.assertEqual(verified['status'],'verified',verified)
                self.assertIs(verified['task_success'],True,verified)
                artifact_bytes=artifact_path.read_bytes()
                expected_fods=calc_tests._CALC_TASK_FODS.replace(
                    b'office:value="731"',
                    ('office:value="'+task_values['A1']+'"').encode())
                expected_fods=expected_fods.replace(b'office:value="864"',
                    ('office:value="'+task_values['A2']+'"').encode())
                self.assertEqual(artifact_bytes,expected_fods)
                root_xml=ET.fromstring(artifact_bytes)
                office='urn:oasis:names:tc:opendocument:xmlns:office:1.0'
                values=[cell.attrib.get(f'{{{office}}}value') for cell in
                    root_xml.iter() if cell.tag.endswith('table-cell') and
                    cell.attrib.get(f'{{{office}}}value') is not None]
                self.assertEqual(values,[task_values['A1'],task_values['A2']])
                recorder.record_task_score('stdlib-fods-cell-values-v1',
                    values==[task_values['A1'],task_values['A2']],artifact_bytes)

                # A repaired semantic plan must cross another owner boundary
                # without carrying the prior artifact, target, scope, or aliases.
                warm_values={'A1':'11223','A2':'44556'}
                warm_root=root/'post-repair-warm-owner'; warm_root.mkdir()
                (warm_root/'calc-task-values.json').write_text(
                    json.dumps(warm_values),encoding='utf-8')
                (warm_root/'calc-profile-mode').write_text('enabled',encoding='utf-8')
                (warm_root/'fake-target-exit-receipt').write_text(
                    'enabled',encoding='utf-8')
                (warm_root/'fake-calc-save-writes-artifact').write_text(
                    'enabled',encoding='utf-8')
                (warm_root/'fake-calc-record-point-resolution').write_text(
                    'enabled',encoding='utf-8')
                (warm_root/'fake-process-incarnation').write_text(
                    process_incarnation_from_identity(4322,98766),
                    encoding='ascii')
                (warm_root/'fake-process-generation').write_text(
                    process_generation_from_identity(20,4322,98766),
                    encoding='ascii')
                (warm_root/'fake-window-incarnation').write_text(
                    'a'*64,encoding='ascii')
                (warm_root/'fake-process-pid').write_text('4322',encoding='ascii')
                (warm_root/'fake-process-start-ticks').write_text(
                    '98766',encoding='ascii')
                warm_server=create_server({'app':20},warm_root,
                    session_mode='guarded-x11',guarded_process_identity=True,
                    guarded_query_worker=True,guarded_window_lifecycle=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
                warm_closed=False
                try:
                    warm_prepared_response=await warm_server.call_tool(
                        'interface_guarded_calc_prepare',{
                            'attempt_id':'calc-wait-attempt-03',
                            'task_values':warm_values,'task_plan':task_plan})
                    warm_prepared=json.loads(warm_prepared_response.content[0].text)
                    self.assertEqual(warm_prepared['status'],'prepared',
                                     warm_prepared)
                    self.assertEqual(warm_prepared['task_plan_sha256'],
                                     prepared['task_plan_sha256'],warm_prepared)
                    warm_observed_response=await warm_server.call_tool(
                        'interface_guarded_observe',{})
                    warm_observed=json.loads(warm_observed_response.content[0].text)
                    warm_source=warm_observed['source']
                    warm_entry_name='entry_postrepair'
                    warm_save_name='save_postrepair'
                    warm_entry_response=await warm_server.call_tool(
                        'interface_guarded_mint',{
                            'alias':warm_entry_name,
                            'source_sequence':warm_source['sequence'],
                            'point':[16,31],'region_size':[24,16],
                            'freshness_ms':5000})
                    warm_save_response=await warm_server.call_tool(
                        'interface_guarded_mint',{
                            'alias':warm_save_name,
                            'source_sequence':warm_source['sequence'],
                            'point':[200,205],'region_size':[16,12],
                            'freshness_ms':5000})
                    warm_entry=json.loads(warm_entry_response.content[0].text)
                    warm_save=json.loads(warm_save_response.content[0].text)
                    self.assertEqual(warm_entry['status'],'minted',warm_entry)
                    self.assertEqual(warm_save['status'],'minted',warm_save)
                    warm_result_response=await warm_server.call_tool(
                        'interface_guarded_calc_compiled',{
                            'profile_id':'calc-ocr-save-v1',
                            'bindings':{
                                'entry':{'alias':warm_entry_name,
                                         'offset':warm_entry['offset']},
                                'save':{'alias':warm_save_name,
                                        'offset':warm_save['offset']}},
                            'reviewed_sequence':warm_source['sequence'],
                            'reviewed_artifact_sha256':warm_source[
                                'native']['artifact']['sha256'],
                            'blank_reviewed':True,
                            'attempt_id':'calc-wait-attempt-03',
                            'prepared_call_id':warm_prepared['call_id'],
                            'wait_for_result_ms':10000})
                    warm_result=json.loads(warm_result_response.content[0].text)
                    self.assertIn('method_receipt',warm_result,warm_result)
                    self.assertEqual(warm_result['method_receipt'][
                        'task_plan_sha256'],prepared['task_plan_sha256'],
                        warm_result)
                    self.assertEqual(warm_result['method_receipt'][
                        'completed_transitions'],2,warm_result)
                    self.assertTrue(all(row['release_verified'] is True for row in
                        warm_result['method_receipt']['transitions']),warm_result)
                    self.assertIsNone(warm_result['task_success'],warm_result)
                    warm_close_response=await warm_server.call_tool(
                        'interface_close',{})
                    warm_close=json.loads(warm_close_response.content[0].text)
                    warm_closed=True
                    self.assertTrue(warm_close['verified'],warm_close)
                    self.assertTrue(warm_close['release_confirmed'],warm_close)
                    warm_artifact=Path(warm_prepared['artifact_path'])
                    self.assertTrue(warm_artifact.is_file(),warm_artifact)
                    warm_verify_response=await warm_server.call_tool(
                        'interface_verify_task',{'call_id':warm_result['call_id']})
                    warm_verified=json.loads(warm_verify_response.content[0].text)
                    self.assertEqual(warm_verified['status'],'verified',
                                     warm_verified)
                    self.assertIs(warm_verified['task_success'],True,warm_verified)
                    self.assertEqual(warm_verified['task_effect']['parsed_effect'][
                        'cells'],warm_values,warm_verified)
                    self.assertNotEqual(warm_prepared['call_id'],prepared['call_id'])
                    self.assertNotEqual(str(warm_artifact),str(artifact_path))
                    self.assertNotEqual(warm_source['sequence'],fresh['source'][
                        'sequence'])
                    for generation in ('process_generation','window_generation'):
                        self.assertNotEqual(warm_source['pointer_binding'][generation],
                            fresh['source']['pointer_binding'][generation])
                    self.assertNotEqual(warm_result['method_receipt'][
                        'task_plan_interface']['session_scope'],
                        result['method_receipt']['task_plan_interface'][
                            'session_scope'])
                    warm_interface=warm_result['method_receipt'][
                        'task_plan_interface']
                    repaired_interface=result['method_receipt'][
                        'task_plan_interface']
                    for symbol in ('cell_entry','save_control'):
                        self.assertNotEqual(warm_interface['symbols'][symbol][
                            'target_reference'],
                            repaired_interface['symbols'][symbol][
                                'target_reference'])
                    post_repair_reuse={'attempt_id':'calc-wait-attempt-03',
                        'plan_origin':'prior_attempt_reuse',
                        'plan_source_attempt_id':'calc-wait-attempt-02',
                        'plan_sha256':warm_prepared['task_plan_sha256'],
                        'provider_generation_count':0,
                        'provider_usage':'not measured; no provider was invoked',
                        'task_values':warm_values,'observed_source':warm_source,
                        'prepared':warm_prepared,'result':warm_result,
                        'close':warm_close,'verification':warm_verified}
                finally:
                    if not warm_closed:
                        await warm_server.call_tool('interface_close',{})

                stale_alias_values={'A1':'66778','A2':'99001'}
                stale_alias_root=root/'stale-alias-owner'; stale_alias_root.mkdir()
                (stale_alias_root/'calc-task-values.json').write_text(
                    json.dumps(stale_alias_values),encoding='utf-8')
                (stale_alias_root/'calc-profile-mode').write_text(
                    'enabled',encoding='utf-8')
                (stale_alias_root/'fake-target-exit-receipt').write_text(
                    'enabled',encoding='utf-8')
                (stale_alias_root/'fake-calc-save-writes-artifact').write_text(
                    'enabled',encoding='utf-8')
                (stale_alias_root/'fake-calc-record-point-resolution').write_text(
                    'enabled',encoding='utf-8')
                stale_pid,stale_ticks=4323,98767
                (stale_alias_root/'fake-process-generation').write_text(
                    process_generation_from_identity(20,stale_pid,stale_ticks),
                    encoding='ascii')
                (stale_alias_root/'fake-process-incarnation').write_text(
                    process_incarnation_from_identity(stale_pid,stale_ticks),
                    encoding='ascii')
                (stale_alias_root/'fake-process-pid').write_text(
                    str(stale_pid),encoding='ascii')
                (stale_alias_root/'fake-process-start-ticks').write_text(
                    str(stale_ticks),encoding='ascii')
                (stale_alias_root/'fake-window-incarnation').write_text(
                    'b'*64,encoding='ascii')
                stale_alias_server=create_server({'app':20},stale_alias_root,
                    session_mode='guarded-x11',guarded_process_identity=True,
                    guarded_query_worker=True,guarded_window_lifecycle=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
                stale_alias_closed=False
                try:
                    stale_prepared_response=await stale_alias_server.call_tool(
                        'interface_guarded_calc_prepare',{
                            'attempt_id':'calc-wait-attempt-04',
                            'task_values':stale_alias_values,'task_plan':task_plan})
                    stale_prepared=json.loads(stale_prepared_response.content[0].text)
                    self.assertEqual(stale_prepared['status'],'prepared',
                                     stale_prepared)
                    stale_observed_response=await stale_alias_server.call_tool(
                        'interface_guarded_observe',{})
                    stale_observed=json.loads(stale_observed_response.content[0].text)
                    stale_source=stale_observed['source']
                    stale_alias_response=await stale_alias_server.call_tool(
                        'interface_guarded_calc_compiled',{
                            'profile_id':'calc-ocr-save-v1',
                            'bindings':new_bindings,
                            'reviewed_sequence':stale_source['sequence'],
                            'reviewed_artifact_sha256':stale_source[
                                'native']['artifact']['sha256'],
                            'blank_reviewed':True,
                            'attempt_id':'calc-wait-attempt-04',
                            'prepared_call_id':stale_prepared['call_id'],
                            'wait_for_result_ms':10000})
                    stale_alias=json.loads(stale_alias_response.content[0].text)
                    self.assertEqual(stale_alias['status'],'invalid_request',
                                     stale_alias)
                    self.assertEqual(stale_alias['error'],
                        'CALC_BINDING_NOT_MINTED_FOR_REVIEWED_SOURCE',
                        stale_alias)
                    self.assertFalse(stale_alias['operation_invoked'],
                                     stale_alias)
                    self.assertFalse(stale_alias['input_dispatched'],
                                     stale_alias)
                    self.assertIsNone(stale_alias['release_confirmed'],
                                      stale_alias)
                    self.assertFalse(stale_alias['replay_allowed'],stale_alias)
                    self.assertFalse(list(stale_alias_root.rglob(
                        'calc-fake-state.json')),
                        'stale aliases must be refused before Fake X receives input')
                    local_aliases={}
                    for name,point,size in (
                            ('local_entry',[16,31],[24,16]),
                            ('local_save',[200,205],[16,12])):
                        minted_response=await stale_alias_server.call_tool(
                            'interface_guarded_mint',{
                                'alias':name,
                                'source_sequence':stale_source['sequence'],
                                'point':point,'region_size':size,
                                'freshness_ms':5000})
                        local_aliases[name]=json.loads(
                            minted_response.content[0].text)
                        self.assertEqual(local_aliases[name]['status'],'minted',
                                         local_aliases[name])
                    reobserved_response=await stale_alias_server.call_tool(
                        'interface_guarded_observe',{})
                    reobserved=json.loads(reobserved_response.content[0].text)
                    self.assertGreater(reobserved['source']['sequence'],
                                       stale_source['sequence'],reobserved)
                    stale_frame_response=await stale_alias_server.call_tool(
                        'interface_guarded_calc_compiled',{
                            'profile_id':'calc-ocr-save-v1',
                            'bindings':{
                                'entry':{'alias':'local_entry','offset':
                                    local_aliases['local_entry']['offset']},
                                'save':{'alias':'local_save','offset':
                                    local_aliases['local_save']['offset']}},
                            'reviewed_sequence':stale_source['sequence'],
                            'reviewed_artifact_sha256':stale_source[
                                'native']['artifact']['sha256'],
                            'blank_reviewed':True,
                            'attempt_id':'calc-wait-attempt-04-stale-frame',
                            'prepared_call_id':stale_prepared['call_id'],
                            'wait_for_result_ms':10000})
                    stale_frame=json.loads(stale_frame_response.content[0].text)
                    self.assertEqual(stale_frame['status'],'invalid_request',
                                     stale_frame)
                    self.assertEqual(stale_frame['error'],
                        'CALC_REVIEW_SOURCE_STALE',stale_frame)
                    self.assertFalse(stale_frame['operation_invoked'],stale_frame)
                    self.assertFalse(stale_frame['input_dispatched'],stale_frame)
                    self.assertFalse(list(stale_alias_root.rglob(
                        'calc-fake-state.json')),
                        'superseded observation must be refused before owner runtime')
                    stale_alias_close_response=await stale_alias_server.call_tool(
                        'interface_close',{})
                    stale_alias_close=json.loads(
                        stale_alias_close_response.content[0].text)
                    stale_alias_closed=True
                    self.assertTrue(stale_alias_close['verified'],
                                    stale_alias_close)
                    self.assertIsNone(stale_alias_close['release_confirmed'],
                        'owner close stays conservative even though MCP preflight '
                        'proves no runtime call was submitted: '
                        +repr(stale_alias_close))
                    stale_alias_rejection={'attempt_id':'calc-wait-attempt-04',
                        'plan_origin':'prior_attempt_reuse',
                        'plan_source_attempt_id':'calc-wait-attempt-02',
                        'plan_sha256':stale_prepared['task_plan_sha256'],
                        'stale_bindings':new_bindings,
                        'observed_source':stale_source,
                        'runtime_result':stale_alias,
                        'same_owner_superseded_frame':{
                            'old_source':stale_source,
                            'latest_source':reobserved['source'],
                            'old_source_mints':local_aliases,
                            'result':stale_frame},
                        'fake_input_state_created':False,
                        'close':stale_alias_close,
                        'task_score':'not_run; MCP preflight refused before owner runtime',
                        'release_interpretation':'unknown in owner close receipt; '
                            'the MCP boundary independently proves operation_invoked=false'}
                finally:
                    if not stale_alias_closed:
                        await stale_alias_server.call_tool('interface_close',{})

                receipt=recorder.reconcile(); summary=summarize(receipt['events'])
                self.assertTrue(receipt['complete'])
                self.assertEqual(summary['model_attempt_count'],3)
                self.assertEqual(summary['usage_status'],'complete')
                self.assertEqual(summary['input_tokens'],150)
                self.assertEqual(summary['output_tokens'],33)
                self.assertEqual(summary['task_success'],True)
                self.assertEqual([event['attempt_id'] for event in receipt['events']
                    if event['kind']=='model_attempt'],
                    ['calc-wait-attempt-01','calc-wait-attempt-02',
                     'calc-wait-attempt-03'])
                self.assertTrue(phase_ns)
                self.assertEqual(set(phase_ns),{
                    'initial_observe','initial_mint',
                    'provider_wait_including_stale_observation',
                    'stale_generation_to_refusal','fresh_observe',
                    'fresh_mint','provider_authored_prepare',
                    'fresh_provider_to_compiled_result',
                    'compiled_graph_runtime','neutral_close',
                    'post_close_independent_score'},phase_ns)
                self.assertTrue(all(type(value) is int and value >= 0
                                    for value in phase_ns.values()),phase_ns)

                retained=os.environ.get('AGENT_INTERFACE_RETAIN_CALC_PROVIDER_WAIT_EVIDENCE')
                if retained:
                    destination=Path(retained).resolve(); destination.mkdir(parents=True,exist_ok=False)
                    shutil.copytree(recorder.root,destination/'provider-ledger')
                    shutil.copytree(root/'provider-call',destination/'provider-call')
                    shutil.copytree(server_root,destination/'server-runtime')
                    shutil.copytree(warm_root,
                                    destination/'post-repair-warm-owner')
                    shutil.copytree(stale_alias_root,
                                    destination/'stale-alias-owner')
                    shutil.copy2(old_image,destination/'source-before-wait.png')
                    shutil.copy2(changed_image,
                                 destination/'source-during-wait-change.png')
                    shutil.copy2(fresh_image,
                                 destination/'source-after-repair.png')
                    shutil.copy2(journal,destination/'app-server-protocol.jsonl')
                    report={'schema':'agent-interface/calc-provider-wait-repair-reuse-v1',
                        'provider_attempts':3,'first_stale_response':first_body,
                        'environment':{'provider':'FakePlanner','target':'FakeX Calc fixture',
                            'runtime':'Windows owned guarded-X11 composition',
                            'python_version':sys.version,
                            'optimization_level':sys.flags.optimize,
                            'test_command':('python -O' if sys.flags.optimize else 'python')
                                +' -m unittest -k calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py',
                            'task_values':task_values,
                            'plan_sha256':prepared['task_plan_sha256'],
                            'timing_note':'monotonic phase diagnostics only; provider wait and usage are synthetic; no warm-vs-cold efficiency comparison'},
                        'first_attempt_had_fake_input_state':False,
                        'fresh_sequence_after_wait':fresh['source']['sequence'],
                        'repaired_execution_result':result,'owner_close':closed,
                        'task_artifact_origin':'Fake X Calc wrote fixture FODS on Ctrl+S before interface_close',
                        'task_effect_from_calc_operation':True,
                        'live_calc_task_effect':False,
                        'task_verification':verified,'independent_fods_values':values,
                        'stale_source':old_source,
                        'changed_source_during_provider_wait':changed_source,
                        'repair_source':fresh['source'],
                        'post_repair_reuse':post_repair_reuse,
                        'stale_alias_rejection':stale_alias_rejection,
                        'joined_summary':summary,
                        'synthetic_phase_durations_ns':phase_ns,
                        'source_sha256':{name:hashlib.sha256(
                            (Path(__file__).resolve().parents[3]/name).read_bytes()
                            ).hexdigest() for name in (
                                'research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py',
                                'research/integration/standard_mcp_task_ledger_57_v1/app_server_provider_to_public_mcp_v1.py',
                                'runtime/cli_v1/mcp_server.py',
                                'runtime/cli_v1/mcp_guarded.py',
                                'runtime/guarded_x11_v1/calc_symbolic_plan_v1.py',
                                'runtime/guarded_x11_v1/calc_profile_v1.py')},
                        'timing_scope':'Windows monotonic wall time, FakePlanner/FakeX; provider wait is injected and token/price values are synthetic; phase durations are not matched efficiency evidence',
                        'limits':['FakePlanner_only','FakeX_only',
                                  'no_live_provider','no_live_Calc','no_efficiency_claim']}
                    (destination/'boundary-results.json').write_text(json.dumps(
                        report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
            finally:
                release_provider.set()
                await server.call_tool('interface_close',{})


if __name__ == "__main__":
    unittest.main()
