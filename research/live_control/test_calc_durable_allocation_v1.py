import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.live_control.adaptive_acquisition_caller_v3 import ModelFailure
from research.live_control.calc_durable_allocation_v1 import (
    DurableCalcAllocation, audit_allocation,
)
from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation


SOURCE = hashlib.sha256(b"frozen calc source").hexdigest()
SOURCE_HASHES = {"caller.py": hashlib.sha256(b"caller source").hexdigest()}
OBSERVATIONS = ["capture-17", "capture-18"]
SPEC = {"target": "Calc", "route": "cold",
        "coarse_origin": "model_produced", "provided_coarse": None,
        "cached_target": None, "local_repair_on": [], "repair_on": [],
        "session_id": "offline-calc-durable"}


def allocation(root, name="attempt-001"):
    return DurableCalcAllocation(root, name, source_sha256=SOURCE,
        observation_ids=OBSERVATIONS, source_hashes=SOURCE_HASHES,
        conditions={"model": "fixture-model", "effort": "low",
                    "route": "cold", "task": "two-cell-save"})


def model_result(output, call_id):
    return {"call_id": call_id, "output": output,
            "usage": {"input_tokens": 120, "cached_input_tokens": 20,
                      "output_tokens": 12, "reasoning_output_tokens": 4},
            "requested_model": "fixture-model", "requested_effort": "low",
            "cost": 0.01, "visible_images_submitted": 1, "wait_ns": 50}


def caller_adapters(*, verify=None, anchor=None, coarse=None, journal=None):
    target = {"handle": "save", "point": [20, 30]}
    result = {
        "observe_source": lambda _payload: {"sequence": 17, "capture_ns": 100},
        "coarse_model": lambda payload: (coarse(payload) if callable(coarse) else coarse) if coarse is not None else model_result(
            {"status": "candidate", "point": [20, 30]}, "coarse-1"),
        "acquire_anchor": lambda _payload: {"image_ref": "anchor-17"},
        "anchor_model": lambda _payload: (anchor or model_result(
            {"status": "target_reference", "target": target}, "anchor-1")),
        "final_revalidate": lambda _payload: {"status": "revalidated"},
        "verify_effect": verify or (lambda _payload: {
            "status": "succeeded", "evidence_ref": "artifact://saved-workbook",
            "evidence_digest": "b" * 64, "effect_scope": "two expected cells"}),
    }
    if journal is not None:
        result["journal"] = journal
    return result


def run_case(ledger, adapters, *, executor=None):
    interface_for_target = lambda payload: {
        "interface_id": "calc-g10-graph-01", "target": payload["target"]}
    receipt = {"outcome": "TASK_SUCCEEDED", "completed_transitions": 2,
               "critical_events": [{"event": "action_terminal",
                                    "input_dispatched": True}]}
    with patch("research.live_control.calc_g10_caller_v1.run_with_bounded_fresh_proposal",
               side_effect=executor or (lambda *args, **kwargs: receipt)):
        return run_g10_in_durable_allocation(SPEC, adapters,
            interface_for_target, object(), {}, ledger,
            perceive=lambda *_: {}, verify_effect=lambda *_: {},
            proposal_worker=object(), cancelled=lambda: False)


class DurableCalcAllocationTests(unittest.TestCase):
    def test_receipt_usage_and_effect_are_durable_before_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = allocation(root)
            order = []
            adapters = caller_adapters(journal=lambda event: order.append(event["event"]))
            original_verify = adapters["verify_effect"]
            def verify(payload):
                self.assertTrue((ledger.path / "compiled_receipt.json").is_file())
                order.append("effect_verifier_called")
                return original_verify(payload)
            adapters["verify_effect"] = verify

            result = run_case(ledger, adapters)

            self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
            self.assertEqual(order.count("effect_verifier_called"), 1)
            report = audit_allocation(ledger.path)
            self.assertEqual((report["status"], report["outcome"]),
                             ("audited", "TASK_SUCCEEDED"))
            self.assertTrue(report["receipt_persisted"])
            self.assertTrue(report["effect_receipt_persisted"])
            saved = json.loads((ledger.path / "result.json").read_text())
            self.assertEqual(saved["accounting"]["attempted_calls"], 2)
            self.assertEqual(saved["accounting"]["usage_totals"]["input_tokens"], 240)
            self.assertEqual(saved["accounting"]["cost_coverage"], 2)
            self.assertEqual(saved["accounting"]["cost"], 0.02)
            self.assertEqual(len(saved["model_call_cost_ledger"]), 2)
            self.assertFalse(saved["model_outputs_retained"])
            self.assertEqual(saved["observation_ids"], OBSERVATIONS)

    def test_timed_out_model_attempt_usage_is_retained_as_not_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            failure = ModelFailure("provider deadline", call_id="coarse-timeout",
                thread_id="thread-1", usage={"input_tokens": 120,
                "cached_input_tokens": 20, "output_tokens": 0,
                "reasoning_output_tokens": 0}, requested_model="fixture-model",
                requested_effort="low", visible_images_submitted=1,
                wait_ns=100, cost=0.03, typed_status="DEFERRED_UPSTREAM")
            adapters = caller_adapters(coarse=lambda _payload: (_ for _ in ()).throw(failure))

            result = run_case(ledger, adapters)

            self.assertEqual(result["outcome"], "TASK_DEFERRED")
            self.assertEqual(result["accounting"]["attempted_calls"], 1)
            self.assertEqual(result["attempt_ledger"][0]["status"], "failed")
            self.assertEqual(result["attempt_ledger"][0]["call_id"], "coarse-timeout")
            self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 120)
            self.assertEqual(result["attempt_ledger"][0]["cost"], 0.03)
            self.assertEqual(result["accounting"]["cost"], 0.03)
            report = audit_allocation(ledger.path)
            self.assertEqual(report["outcome"], "TASK_DEFERRED")
            self.assertFalse(report["receipt_persisted"])

    def test_receipt_write_failure_prevents_outer_effect_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            verified = []
            adapters = caller_adapters(verify=lambda _payload: verified.append(True) or {
                "status": "succeeded"})
            ledger.persist_execution_receipt = lambda _receipt: (_ for _ in ()).throw(
                OSError("disk full"))

            result = run_case(ledger, adapters)

            self.assertEqual(result["outcome"], "CALLER_FAILED")
            self.assertEqual(verified, [])
            report = audit_allocation(ledger.path)
            self.assertEqual(report["outcome"], "CALLER_FAILED")
            self.assertFalse(report["receipt_persisted"])
            self.assertFalse(report["effect_receipt_persisted"])

    def test_interruption_retains_unknown_allocation_without_success_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            adapters = caller_adapters()
            def interrupt(*_args, **_kwargs):
                raise KeyboardInterrupt()

            with self.assertRaises(KeyboardInterrupt):
                run_case(ledger, adapters, executor=interrupt)

            report = audit_allocation(ledger.path)
            self.assertEqual(report["status"], "UNKNOWN")
            events = [json.loads(line) for line in
                      (ledger.path / "events.jsonl").read_text().splitlines()]
            self.assertEqual(events[-1]["event_type"], "caller_aborted")
            self.assertFalse((ledger.path / "result.json").exists())

    def test_torn_event_tail_is_unknown_not_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            ledger.append_event("test", {"value": 1})
            path = ledger.path / "events.jsonl"
            with path.open("ab") as stream:
                stream.write(b'{"partial":')
            with self.assertRaisesRegex(ValueError, "torn event log"):
                audit_allocation(ledger.path)

    def test_result_rewrite_is_detected_by_terminal_event_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            run_case(ledger, caller_adapters())
            path = ledger.path / "result.json"
            result = json.loads(path.read_text())
            result["reason"] = "rewritten after finalization"
            path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False) + "\n")
            with self.assertRaisesRegex(ValueError, "terminal event/result mismatch"):
                audit_allocation(ledger.path)

    def test_condition_rewrite_is_detected_by_creation_event_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            run_case(ledger, caller_adapters())
            path = ledger.path / "conditions.json"
            manifest = json.loads(path.read_text())
            manifest["conditions"]["model"] = "rewritten-model"
            path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False) + "\n")
            with self.assertRaisesRegex(ValueError, "allocation manifest/event mismatch"):
                audit_allocation(ledger.path)

    def test_interface_binding_rewrite_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = allocation(Path(tmp))
            run_case(ledger, caller_adapters())
            path = ledger.path / "interface_binding.json"
            binding = json.loads(path.read_text())
            binding["interface_id"] = "rewritten-interface"
            path.write_text(json.dumps(binding, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False) + "\n")
            with self.assertRaisesRegex(ValueError, "interface binding event/file mismatch"):
                audit_allocation(ledger.path)


if __name__ == "__main__":
    unittest.main()
