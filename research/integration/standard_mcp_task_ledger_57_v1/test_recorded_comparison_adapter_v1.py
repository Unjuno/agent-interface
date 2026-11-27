"""Exercise the caller-journal to matched-comparison adapter offline."""

import asyncio
import base64
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from comparison_measurement_v1 import validate_matched_block, validate_measured_run
from ledger import LedgerValidationError
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_comparison_adapter_v1 import build_measured_run
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller


class SyntheticLateUsageSource:
    def __init__(self, available, *, input_tokens=18, turn_id="turn-fixture"):
        self.available = available
        self.read_count = 0
        self.provider_identity = {"thread_id": "thread-fixture", "turn_id": turn_id}
        self.usage = {"status": "reported", "input_tokens": input_tokens,
                      "output_tokens": 3}
        self.usage_bytes = json.dumps(
            self.usage, sort_keys=True, separators=(",", ":")).encode()
        self.source_bytes = json.dumps({
            "direction": "received", "observed_ns": 10000,
            "message": {"method": "thread/tokenUsage/updated",
                        "params": {"threadId": "thread-fixture",
                                   "turnId": turn_id,
                                   "tokenUsage": {"last": {
                                       "inputTokens": input_tokens,
                                       "outputTokens": 3}}}},
        }, sort_keys=True, separators=(",", ":")).encode() + b"\n"

    def read(self, _timeout):
        self.read_count += 1
        if not self.available or self.read_count > 1:
            return None
        return {"usage": self.usage, "usage_bytes": self.usage_bytes,
                "source_bytes": self.source_bytes, "observed_ns": 10000}


class UnusedRelay:
    async def request(self, _request_bytes):
        raise AssertionError("late-usage observation must not submit Relay calls")


class RecordedComparisonAdapterTests(unittest.TestCase):
    @classmethod
    def make_run(cls, *args, **kwargs):
        return build_measured_run(**cls.make_inputs(*args, **kwargs))

    @staticmethod
    def make_inputs(root: Path, arm: str, order: int, *,
                 effect_observed_ns=130, owner_variant=None,
                 late_usage_available=None, public_observation=False):
        ticks = iter(range(100, 300, 10))
        recorder = ProviderAttemptRecorder(root / "recorder",
                                           clock_ns=lambda: next(ticks))
        recorder.session_id = hashlib.sha256(
            f"adapter-fixture-session-{arm}".encode()).hexdigest()[:32]
        response = b'{"assistant":"observe"}\n'
        usage = {"status": "reported", "input_tokens": 10,
                 "output_tokens": 2}
        if late_usage_available is not None:
            unavailable = {"status": "unavailable", "input_tokens": None,
                           "output_tokens": None}
            caller = RecordedPublicMcpCaller(
                UnusedRelay(), recorder, allowed_methods={"interface_dispatch"})

            async def timed_out_provider():
                source = SyntheticLateUsageSource(late_usage_available)
                return {"status": "timeout", "usage": unavailable,
                        "provider_identity": source.provider_identity, "late_usage_source": source}

            timed_out = asyncio.run(caller.invoke_provider(
                "attempt-late-usage", b'{"prompt":"timed out"}\n', timed_out_provider))
        recorder.invoke("attempt-1", b'{"prompt":"frozen"}\n',
                        lambda: {"status": "completed", "usage": usage,
                                 "response_bytes": response})
        png = None
        observation_id = None
        target_generation = None
        if public_observation:
            png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9WQAAAAASUVORK5CYII=")
            local_image_digest = hashlib.sha256(png).hexdigest()
            observation_id = "9" * 32
            target_generation = "c" * 64
            observation_report = {
                "schema": "agent-interface/runtime-observation-v1",
                "status": "returned", "observation_id": observation_id,
                "side_effect_authority": False, "input_dispatched": False,
                "target_generation": target_generation,
                "target_generation_consistency": "matched",
                "observation": {"capture_started_ns": 121,
                                "capture_ended_ns": 125,
                                "artifact": {"mime_type": "image/png",
                                             "bytes": len(png),
                                             "sha256": local_image_digest}},
            }
            tool_response = {
                "status": "returned", "tool": "interface_observe",
                "result": {"content": [
                    {"type": "text", "text": json.dumps(
                        observation_report, sort_keys=True,
                        separators=(",", ":"))},
                    {"type": "image", "mimeType": "image/png",
                     "data": base64.b64encode(png).decode("ascii")},
                ]},
            }
            observation_method = "interface_observe"
        else:
            tool_response = {"source": {"sequence": 1}}
            observation_method = "interface_guarded_observe"
        tool_response_bytes = json.dumps(
            tool_response, separators=(",", ":"), sort_keys=True).encode()
        recorder.invoke_tool(
            "attempt-1", "observe-1", observation_method,
            json.dumps({"tool": observation_method}, sort_keys=True).encode(),
            lambda: {"result": tool_response,
                     "response_bytes": tool_response_bytes})
        action_call_id = "a" * 32
        action_operation_id = "b" * 32
        target_generation = "c" * 64
        owner_result = {
            "operation_id": action_operation_id,
            "target_generation": target_generation,
            "phase": "recovered",
            "status": "recovered",
            "deadline_ns": 150,
            "release_confirmed": True,
            "late_input_horizon_verified": True,
            "late_input_release_received_ns": 155,
            "late_input_horizon_ns": 5,
            "late_input_observation_start_ns": 155,
            "late_input_observation_end_ns": 160,
            "late_input_observation_count": 2,
            "late_input_max_observed_gap_ns": 5,
            "late_input_max_sample_gap_ns": 5,
        }
        cancellation = {
            "operation_id": "d" * 32,
            "action_operation_id": action_operation_id,
            "target_generation": target_generation,
            "status": "recovered",
            "release_confirmed": True,
            "result": owner_result,
        }
        if owner_variant == "wrong_generation":
            cancellation["target_generation"] = "e" * 64
        elif owner_variant == "unverified_horizon":
            owner_result["late_input_horizon_verified"] = False
        public_receipt = {
            "call_id": action_call_id,
            "action": {"operation_id": action_operation_id,
                       "target_generation": target_generation,
                       "status": "unknown"},
            "cancellation": cancellation,
        }
        public_response = {
            "status": "returned", "tool": "interface_results",
            "result": {"content": [{"type": "text",
                         "text": json.dumps(public_receipt,
                                             sort_keys=True,
                                             separators=(",", ":"))}]},
        }
        public_response_bytes = json.dumps(
            public_response, sort_keys=True, separators=(",", ":")).encode()
        dispatch_body = {
            "call_id": action_call_id,
            "operation_id": ("f" * 32 if owner_variant == "wrong_action_operation"
                              else action_operation_id),
            "target_generation": target_generation,
            "status": "unknown",
            "task_success": None,
            "replay_allowed": False,
        }
        dispatch_response = {
            "status": "returned", "tool": "interface_dispatch",
            "result": {"content": [{"type": "text",
                         "text": json.dumps(dispatch_body,
                                             sort_keys=True,
                                             separators=(",", ":"))}]},
        }
        recorder.invoke_tool(
            "attempt-1", action_call_id, "interface_dispatch",
            json.dumps({"tool": "interface_dispatch", "arguments": {
                "program": {"authority": {"expires_at_ns": 150}}}},
                sort_keys=True, separators=(",", ":")).encode(),
            lambda: {"result": dispatch_response,
                     "response_bytes": json.dumps(
                         dispatch_response, sort_keys=True,
                         separators=(",", ":")).encode()})
        recorder.invoke_tool(
            "attempt-1", "lookup-results-1", "interface_results",
            json.dumps({"call_id": action_call_id}, sort_keys=True,
                       separators=(",", ":")).encode(),
            lambda: {"result": public_response,
                     "response_bytes": public_response_bytes})
        state = b'{"task_state":"complete"}\n'
        recorder.record_task_score("independent-fixture-oracle-v1", True, state)
        if late_usage_available is not None:
            observed = asyncio.run(caller.observe_late_usage(
                "attempt-late-usage", timed_out, timeout=0))
            if observed["observed"] is not late_usage_available:
                raise AssertionError("late-usage source result differs from arm")
        receipt = recorder.reconcile()

        delivered_image = b"synthetic model-delivered observation"
        image_path = root / "recorder" / "raw" / "model-image.bin"
        image_path.write_bytes(delivered_image)
        image_digest = hashlib.sha256(delivered_image).hexdigest()
        receipt["raw_refs"].append({
            "path": "raw/model-image.bin", "sha256": image_digest})
        if public_observation:
            local_image_path = root / "recorder" / "raw" / "public-observation.png"
            local_image_path.write_bytes(png)
            local_image_digest = hashlib.sha256(png).hexdigest()
            receipt["raw_refs"].append({
                "path": "raw/public-observation.png",
                "sha256": local_image_digest})
        metadata = {
            "schema": "agent-interface/standard-mcp-task-ledger-v1",
            "run_id": f"run-{arm}",
            "comparison": {"arm": arm, "block": 1, "order": order,
                           "task_seed": "fixed-seed"},
            "task": {"task_id": "fixture-task",
                     "fixture_sha256": "a" * 64,
                     "scorer_sha256": "b" * 64},
            "source": {"commit": "c" * 40,
                       "route_sha256": arm.lower() * 64},
            "environment_sha256": "d" * 64,
            "model": {"id": "fixture-model", "effort": "low",
                      "request_config_sha256": "e" * 64},
        }
        run_end_ns = 220 if late_usage_available is not None else 190
        measurement = {
            "started_ns": 95, "ended_ns": run_end_ns,
            "elapsed_ns": run_end_ns - 95,
            "phases": [
                {"name": "setup_acquisition", "started_ns": 95,
                 "ended_ns": 100},
                {"name": "provider_wait", "started_ns": 100,
                 "ended_ns": 110},
                {"name": "observation_grounding", "started_ns": 110,
                 "ended_ns": 140},
                {"name": "local_execution", "started_ns": 140,
                 "ended_ns": 150},
                {"name": "recovery", "started_ns": 150,
                 "ended_ns": 160},
                {"name": "effect_verification", "started_ns": 160,
                 "ended_ns": 180},
                {"name": "cleanup", "started_ns": 180,
                 "ended_ns": run_end_ns},
            ],
            "model_delivered_images": [{"attempt_id": "attempt-1",
                                        "sha256": image_digest}],
            "local_observations": ([{
                "tool_call_id": "observe-1", "observation_id": observation_id,
                "target_generation": target_generation,
                "capture_started_ns": 121, "capture_ended_ns": 125,
                "image_sha256": local_image_digest,
            }] if public_observation else [{
                "tool_call_id": "observe-1", "source_sequence": 1,
                "captured_ns": (145 if late_usage_available is not None else 125),
                "image_sha256": image_digest,
            }]),
            "native_owner_evidence": {
                "lookup_tool_call_id": "lookup-results-1",
                "action_call_id": action_call_id,
                "effect_observed_ns": (145 if effect_observed_ns == 130
                                        else effect_observed_ns),
            },
        }
        return {"receipt": receipt, "recorder_root": root / "recorder",
                "ledger_metadata": metadata, "measurement": measurement}

    def test_three_recorded_caller_runs_form_one_valid_matched_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = [self.make_run(root / arm, arm, index)
                    for index, arm in enumerate(("A", "B", "C"), start=1)]
            result = validate_matched_block(runs)
        self.assertEqual(set(result["arms"]), {"A", "B", "C"})
        for arm in result["arms"].values():
            self.assertEqual(arm["model_attempt_count"], 1)
            self.assertEqual(arm["tool_call_count"], 3)
            self.assertEqual(arm["input_tokens"], 10)
            self.assertTrue(arm["task_success"])
        binding = runs[0]["task_ledger"]["native_owner_binding"]
        self.assertEqual(binding["action_operation_id"], "b" * 32)
        self.assertEqual(binding["target_generation"], "c" * 64)
        self.assertTrue(binding["release_confirmed"])
        self.assertTrue(binding["horizon_verified"])

    def test_dispatch_program_projection_binds_retained_request_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            measured = self.make_run(Path(temporary), "C", 3)
        dispatch = next(event for event in measured["task_ledger"]["events"]
                        if event.get("method") == "interface_dispatch")
        self.assertEqual(dispatch["dispatch_program"]["authority"]["expires_at_ns"],
                         150)
        ref = dispatch["dispatch_program_ref"]
        self.assertIn(ref, measured["task_ledger"]["raw_refs"])

    def test_recorded_adapter_retains_public_win32_observation_png(self):
        with tempfile.TemporaryDirectory() as temporary:
            measured = self.make_run(Path(temporary), "A", 1,
                                     public_observation=True)
        observation = measured["measurement"]["local_observations"][0]
        self.assertEqual(observation["observation_id"], "9" * 32)
        self.assertEqual(observation["target_generation"], "c" * 64)
        self.assertIn(observation["image_sha256"], {
            ref["sha256"] for ref in measured["task_ledger"]["raw_refs"]})
        self.assertEqual(validate_measured_run(measured)["local_observation_count"], 1)

    def test_late_usage_cannot_be_credited_to_another_failed_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            ticks = iter(range(100, 300, 10))
            recorder = ProviderAttemptRecorder(temporary, clock_ns=lambda: next(ticks))
            caller = RecordedPublicMcpCaller(
                UnusedRelay(), recorder, allowed_methods={"interface_dispatch"})
            first_source = SyntheticLateUsageSource(True, input_tokens=18, turn_id="turn-first")
            second_source = SyntheticLateUsageSource(True, input_tokens=31, turn_id="turn-second")

            async def finish_attempt(attempt_id, source):
                async def provider():
                    return {
                        "status": "timeout", "late_usage_source": source,
                        "provider_identity": getattr(source, "provider_identity", None),
                        "usage": {"status": "unavailable", "input_tokens": None, "output_tokens": None},
                    }
                return await caller.invoke_provider(attempt_id, b"fake request", provider)

            async def run():
                first = await finish_attempt("first", first_source)
                second = await finish_attempt("second", second_source)
                unbound_source = SyntheticLateUsageSource(True, turn_id="unknown-turn")
                del unbound_source.provider_identity
                unbound = await finish_attempt("unbound", unbound_source)
                recorder.record_task_score("independent-oracle", True, b"independent state")
                before = recorder.reconcile()
                held = await caller.observe_late_usage("unbound", unbound, timeout=0)
                self.assertEqual(held, {"observed": False, "reason": "provider_identity_unbound"})
                self.assertEqual(unbound_source.read_count, 0)
                with self.assertRaisesRegex(ValueError, "late usage source.*bound"):
                    await caller.observe_late_usage("first", second, timeout=0)
                self.assertEqual(second_source.read_count, 0)
                self.assertEqual(recorder.reconcile(), before)
                await caller.observe_late_usage("first", first, timeout=0)
                await caller.observe_late_usage("second", second, timeout=0)
                return before["events"][-1], recorder.reconcile()

            score, receipt = asyncio.run(run())
        first, second, unbound, retained_score = receipt["events"]
        self.assertEqual([(attempt["attempt_id"], attempt["usage"]["input_tokens"])
                          for attempt in (first, second, unbound)],
                         [("first", 18), ("second", 31), ("unbound", None)])
        self.assertEqual(retained_score, score)

    def test_old_serialized_app_server_usage_cannot_bypass_reconciliation(self):
        retained = (Path(__file__).parent / "postscore_late_usage_measurement_composition_20261121_r02"
                    / "runs/positive")
        receipt = json.loads((retained / "receipt.json").read_bytes())
        measured = json.loads((retained / "measured_run.json").read_bytes())
        self.assertEqual(receipt["events"][0]["usage"]["input_tokens"], 18)
        self.assertIsNone(receipt["events"][-1]["task_success"])
        receipt["events"][-1]["task_success"] = True
        metadata = {key: value for key, value in measured["task_ledger"].items()
                    if key not in ("events", "raw_refs")}
        with tempfile.TemporaryDirectory() as temporary:
            recorder_root = Path(temporary) / "recorder"
            shutil.copytree(retained / "recorder", recorder_root)
            for journal_present in (True, False):
                with self.subTest(journal_present=journal_present):
                    if not journal_present:
                        (recorder_root / "attempts.jsonl").unlink()
                        with self.assertRaisesRegex(LedgerValidationError, "retained journal"):
                            build_measured_run(
                                receipt, recorder_root=recorder_root,
                                ledger_metadata=metadata, measurement=measured["measurement"])
                        continue
                    current = build_measured_run(
                        receipt, recorder_root=recorder_root,
                        ledger_metadata=metadata, measurement=measured["measurement"])
                    summary = validate_measured_run(current)
                    self.assertEqual(summary["usage_status"], "incomplete")
                    self.assertIsNone(summary["input_tokens"])
                    self.assertIsNone(summary["output_tokens"])
                    self.assertEqual(summary["model_attempt_count"], 1)
                    self.assertIsNone(summary["factual_task_success"])
                    self.assertIsNone(summary["task_success"])
                    self.assertEqual(summary["independent_score_status"], "recorded")
                    self.assertEqual(current["task_ledger"]["raw_refs"], receipt["raw_refs"])

    def test_frozen_r02_measurement_composition_with_explicit_synthetic_binding(self):
        packet = Path(__file__).parent / "postscore_late_usage_measurement_composition_20261121_r02"

        def load_module(name, filename):
            spec = importlib.util.spec_from_file_location(name, packet / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        composition = load_module("frozen_r02_composition", "composition.py")
        identity = {"thread_id": "synthetic-thread-57", "turn_id": "synthetic-turn-57"}

        class BoundFixtureCaller(RecordedPublicMcpCaller):
            async def invoke_provider(self, attempt_id, request_bytes, provider_call):
                async def bound_fixture_provider():
                    generation = await provider_call()
                    source = generation["late_usage_source"]
                    if type(source) is not composition.SyntheticLateUsageSource:
                        raise TypeError("expected the pinned fixture source")
                    source.provider_identity = identity
                    return {**generation, "provider_identity": identity}
                return await super().invoke_provider(attempt_id, request_bytes, bound_fixture_provider)

        # Bind the archived synthetic turn outside its hash-pinned fixture and test files.
        with patch.object(composition, "RecordedPublicMcpCaller", BoundFixtureCaller):
            with patch.dict(sys.modules, {"composition": composition}):
                frozen_tests = load_module("frozen_r02_tests", "test_composition.py")
            result = unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromModule(frozen_tests).run(result)
        self.assertEqual(result.testsRun, 2)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)

    def test_late_usage_composes_with_identity_bound_native_owner_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = self.make_run(Path(temporary), "A", 1,
                                late_usage_available=True)
            summary = validate_measured_run(run)
        self.assertEqual(summary["model_attempt_count"], 2)
        self.assertEqual(summary["usage_status"], "complete")
        self.assertEqual(summary["input_tokens"], 28)
        self.assertEqual(summary["output_tokens"], 5)
        self.assertTrue(run["task_ledger"]["native_owner_binding"][
            "release_confirmed"])

    def test_missing_late_usage_stays_incomplete_with_native_owner_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = self.make_run(Path(temporary), "A", 1,
                                late_usage_available=False)
            summary = validate_measured_run(run)
        self.assertEqual(summary["model_attempt_count"], 2)
        self.assertEqual(summary["usage_status"], "incomplete")
        self.assertIsNone(summary["input_tokens"])
        self.assertIsNone(summary["output_tokens"])
        self.assertTrue(run["task_ledger"]["native_owner_binding"][
            "release_confirmed"])

    def test_unknown_native_effect_time_keeps_factual_score_but_blocks_eligibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = self.make_run(Path(temporary), "A", 1,
                                effect_observed_ns=None)
            summary = validate_measured_run(run)
        self.assertTrue(summary["factual_task_success"])
        self.assertIsNone(summary["task_success"])
        self.assertEqual(summary["effect_attribution"]["effect_timing"],
                         "unknown")

    def test_native_effect_after_verified_release_horizon_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = self.make_run(Path(temporary), "A", 1,
                                effect_observed_ns=161)
            summary = validate_measured_run(run)
        self.assertTrue(summary["factual_task_success"])
        self.assertFalse(summary["task_success"])
        self.assertEqual(summary["effect_attribution"]["effect_timing"],
                         "after_release_horizon")
        self.assertEqual(run["task_ledger"]["native_owner_binding"][
            "effect_timing"], "after_release_horizon")

    def test_native_action_generation_mismatch_and_unverified_horizon_fail_closed(self):
        for variant, expected in (
                ("wrong_generation", "does not bind a confirmed recovery"),
                ("unverified_horizon", "release/horizon receipt is missing")):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temporary:
                with self.assertRaisesRegex(LedgerValidationError, expected):
                    self.make_run(Path(temporary), "A", 1,
                                  owner_variant=variant)

    def test_native_action_receipt_must_match_recorded_dispatch_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(LedgerValidationError,
                                        "does not match the recorded dispatch"):
                self.make_run(Path(temporary), "A", 1,
                              owner_variant="wrong_action_operation")

    def test_missing_owner_effect_or_lifecycle_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            measured = self.make_run(root, "A", 1)
            measurement = dict(measured["measurement"])
            del measurement["effect_attribution"]
            receipt = ProviderAttemptRecorder(root / "recorder").reconcile()
            receipt["raw_refs"].append(measured["task_ledger"]["raw_refs"][-1])
            with self.assertRaisesRegex(LedgerValidationError,
                                        "effect evidence are required"):
                build_measured_run(
                    receipt, recorder_root=root / "recorder",
                    ledger_metadata={key: value for key, value in
                                     measured["task_ledger"].items()
                                     if key not in ("events", "raw_refs",
                                                    "native_owner_binding")},
                    measurement=measurement)

    def test_owner_horizon_cannot_be_upgraded_in_serialized_tool_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            inputs = self.make_inputs(Path(temporary), "A", 1,
                                      owner_variant="unverified_horizon")
            with self.assertRaisesRegex(LedgerValidationError, "horizon"):
                build_measured_run(**inputs)

            lookup = next(event for event in inputs["receipt"]["events"]
                          if event.get("method") == "interface_results")
            text = lookup["result"]["result"]["content"][0]
            body = json.loads(text["text"])
            self.assertIs(body["cancellation"]["result"]["late_input_horizon_verified"], False)
            body["cancellation"]["result"]["late_input_horizon_verified"] = True
            text["text"] = json.dumps(body)
            with self.assertRaisesRegex(LedgerValidationError, "public MCP call.*journal"):
                build_measured_run(**inputs)

    def test_omitted_public_tool_call_cannot_enter_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for call_id in ("observe-1", "lookup-results-1"):
                with self.subTest(omitted_call=call_id):
                    inputs = self.make_inputs(root / call_id, "A", 1)
                    # The generic effect projection has no lookup or capture requirement.
                    inputs["measurement"] = build_measured_run(**inputs)["measurement"]
                    if call_id == "observe-1":
                        inputs["measurement"]["local_observations"] = []
                    events = inputs["receipt"]["events"]
                    events[:] = [event for event in events if event.get("call_id") != call_id]
                    for seq, event in enumerate(events, 1):
                        event["seq"] = seq
                    with self.assertRaisesRegex(LedgerValidationError, "public MCP call.*journal"):
                        build_measured_run(**inputs)

    def test_extra_public_tool_call_cannot_enter_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            inputs = self.make_inputs(Path(temporary), "A", 1)
            events = inputs["receipt"]["events"]
            observation = next(event for event in events if event.get("call_id") == "observe-1")
            score = events[-1]
            extra = {**observation, "call_id": "receipt-only-call",
                     "seq": score["seq"], "started_ns": score["started_ns"],
                     "ended_ns": score["started_ns"]}
            score["seq"] += 1
            events.insert(-1, extra)
            with self.assertRaisesRegex(LedgerValidationError, "public MCP call.*journal"):
                build_measured_run(**inputs)

    def test_missing_journal_cannot_certify_public_owner_horizon(self):
        with tempfile.TemporaryDirectory() as temporary:
            inputs = self.make_inputs(Path(temporary), "A", 1)
            measured = build_measured_run(**inputs)
            self.assertTrue(measured["task_ledger"]["native_owner_binding"]["horizon_verified"])
            self.assertTrue(validate_measured_run(measured)["task_success"])
            (inputs["recorder_root"] / "attempts.jsonl").unlink()
            with self.assertRaisesRegex(LedgerValidationError, "public MCP call.*journal"):
                build_measured_run(**inputs)

            # Unchanged raw response files do not prove that the projected
            # workload had zero public calls when the journal is missing.
            receipt = inputs["receipt"]
            retained_refs = list(receipt["raw_refs"])
            receipt["events"] = [event for event in receipt["events"] if event["kind"] != "tool_call"]
            for seq, event in enumerate(receipt["events"], 1):
                event["seq"] = seq
            inputs["measurement"] = {**measured["measurement"], "local_observations": []}
            self.assertEqual(receipt["raw_refs"], retained_refs)
            with self.assertRaisesRegex(LedgerValidationError, "public MCP call.*journal"):
                build_measured_run(**inputs)

    def test_retained_raw_hash_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            measured = self.make_run(root, "A", 1)
            # Change the projection's hash while leaving the journal bytes intact.
            recorder = ProviderAttemptRecorder(root / "recorder")
            receipt = recorder.reconcile()
            receipt["raw_refs"].append(measured["task_ledger"]["raw_refs"][-1])
            receipt["raw_refs"][0] = {
                **receipt["raw_refs"][0], "sha256": "f" * 64}
            with self.assertRaisesRegex(LedgerValidationError,
                                        "digest does not match"):
                build_measured_run(
                    receipt, recorder_root=root / "recorder",
                    ledger_metadata={key: value for key, value in
                                     measured["task_ledger"].items()
                                     if key not in ("events", "raw_refs",
                                                    "native_owner_binding")},
                    measurement=measured["measurement"])

    def test_top_level_receipt_cannot_omit_journal_bound_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            measured = self.make_run(root, "A", 1)
            receipt = ProviderAttemptRecorder(root / "recorder").reconcile()
            receipt["raw_refs"].append(measured["task_ledger"]["raw_refs"][-1])
            receipt["raw_refs"].pop(0)
            with self.assertRaisesRegex(LedgerValidationError,
                                        "omit journal-bound event evidence"):
                build_measured_run(
                    receipt, recorder_root=root / "recorder",
                    ledger_metadata={key: value for key, value in
                                     measured["task_ledger"].items()
                                     if key not in ("events", "raw_refs",
                                                    "native_owner_binding")},
                    measurement=measured["measurement"])

    def test_one_raw_path_cannot_claim_two_digests(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            measured = self.make_run(root, "A", 1)
            receipt = ProviderAttemptRecorder(root / "recorder").reconcile()
            receipt["raw_refs"].append(measured["task_ledger"]["raw_refs"][-1])
            receipt["raw_refs"].append({
                **receipt["raw_refs"][0], "sha256": "f" * 64})
            with self.assertRaisesRegex(LedgerValidationError,
                                        "cannot claim multiple SHA-256"):
                build_measured_run(
                    receipt, recorder_root=root / "recorder",
                    ledger_metadata={key: value for key, value in
                                     measured["task_ledger"].items()
                                     if key not in ("events", "raw_refs",
                                                    "native_owner_binding")},
                    measurement=measured["measurement"])

    def test_incomplete_caller_journal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            measured = self.make_run(root, "A", 1)
            receipt = ProviderAttemptRecorder(
                root / "recorder").reconcile()
            receipt["complete"] = False
            with self.assertRaisesRegex(LedgerValidationError,
                                        "incomplete caller operations"):
                build_measured_run(
                    receipt, recorder_root=root / "recorder",
                    ledger_metadata={key: value for key, value in
                                     measured["task_ledger"].items()
                                     if key not in ("events", "raw_refs")},
                    measurement=measured["measurement"])


if __name__ == "__main__":
    unittest.main()
