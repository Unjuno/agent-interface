import asyncio
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

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


class ProviderToPublicMcpCompositionTests(unittest.IsolatedAsyncioTestCase):
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
