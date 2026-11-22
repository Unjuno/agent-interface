"""Exercise the caller-journal to matched-comparison adapter offline."""

import asyncio
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from comparison_measurement_v1 import validate_matched_block, validate_measured_run
from ledger import LedgerValidationError
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_comparison_adapter_v1 import build_measured_run
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller


class SyntheticLateUsageSource:
    def __init__(self, available):
        self.available = available
        self.read_count = 0
        self.usage = {"status": "reported", "input_tokens": 18,
                      "output_tokens": 3}
        self.usage_bytes = json.dumps(
            self.usage, sort_keys=True, separators=(",", ":")).encode()
        self.source_bytes = json.dumps({
            "direction": "received", "observed_ns": 10000,
            "message": {"method": "thread/tokenUsage/updated",
                        "params": {"threadId": "thread-fixture",
                                   "turnId": "turn-fixture",
                                   "tokenUsage": {"last": {
                                       "inputTokens": 18,
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
    @staticmethod
    def make_run(root: Path, arm: str, order: int, *,
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
            recorder.invoke(
                "attempt-late-usage", b'{"prompt":"timed out"}\n',
                lambda: {"status": "timeout", "usage": unavailable})
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
            b'{"tool":"interface_dispatch"}\n',
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
            caller = RecordedPublicMcpCaller(
                UnusedRelay(), recorder, allowed_methods={"interface_dispatch"})
            observed = asyncio.run(caller.observe_late_usage(
                "attempt-late-usage",
                {"status": "timeout", "late_usage_source":
                 SyntheticLateUsageSource(late_usage_available)}, timeout=0))
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
        return build_measured_run(
            receipt, recorder_root=root / "recorder",
            ledger_metadata=metadata, measurement=measurement)

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
