"""Composition contract for compiled GUI execution inside the shared caller."""

import time
import unittest

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT,
    compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v1 import (
    execute_compiled_interface,
    run_compiled_interface_in_caller,
)


class CompiledExecutionCompositionTests(unittest.TestCase):
    def test_exact_value_path_completes_two_released_actions(self):
        result, receipt = self._run([
            self._predicates(value=False),
            self._predicates(value=True),
            self._predicates(value=True, submitted=True),
        ])

        self.assertEqual(result, {"status": "completed"})
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)
        self.assertEqual([row["action"] for row in receipt["transitions"]],
                         ["enter_token", "submit_form"])
        self.assertTrue(all(row["release_verified"] for row in receipt["transitions"]))

    def test_stale_submit_admission_preserves_one_action_and_stops(self):
        result, receipt = self._run([
            self._predicates(value=False),
            self._predicates(value=True),
        ], refuse="activate_submit")

        self.assertEqual(result, {"status": "safe_yield", "reason": "missing_symbol",
                                  "completed_actions": 1})
        self.assertEqual(receipt["outcome"], "SAFE_YIELD")
        self.assertEqual(receipt["reason"], "missing_symbol")
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertEqual(receipt["transitions"][0]["release_verified"], True)

    def test_unknown_value_yields_without_submit(self):
        result, receipt = self._run([
            self._predicates(value=False),
            self._predicates(value="unknown"),
        ])

        self.assertEqual(result["status"], "safe_yield")
        self.assertEqual(result["reason"], "effect_unavailable")
        self.assertEqual(result["completed_actions"], 1)
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertEqual([row["operation"] for row in self.executed],
                         ["enter_exact_token"])

    def test_caller_composition_preserves_completed_effect_and_accounting(self):
        result, receipt = self._run_through_caller([
            self._predicates(value=False),
            self._predicates(value=True),
            self._predicates(value=True, submitted=True),
        ])

        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["task_effect"], "succeeded")
        self.assertEqual(result["delivery"], "confirmed")
        self.assertEqual(result["execution_progress"], {"status": "completed"})
        self.assertEqual(result["accounting"]["attempted_calls"], 1)
        self.assertEqual(result["accounting"]["completed_calls"], 1)
        self.assertEqual(result["attempt_ledger"][0]["call_id"], "anchor-call")
        self.assertEqual(result["stages"]["execute"]["status"], "completed")
        self.assertEqual(receipt[0]["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt[0]["completed_transitions"], 2)

    def test_caller_composition_propagates_partial_safe_yield(self):
        result, receipt = self._run_through_caller([
            self._predicates(value=False),
            self._predicates(value=True),
        ], refuse="activate_submit")

        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "missing_symbol")
        self.assertEqual(result["delivery"], "confirmed_partial")
        self.assertEqual(result["execution_progress"], {
            "status": "safe_yield", "reason": "missing_symbol",
            "completed_actions": 1})
        self.assertIsNone(result["task_effect"])
        self.assertEqual(result["accounting"]["attempted_calls"], 1)
        self.assertEqual(result["accounting"]["completed_calls"], 1)
        self.assertEqual(receipt[0]["outcome"], "SAFE_YIELD")
        self.assertEqual(receipt[0]["completed_transitions"], 1)
        self.assertNotIn("verify_effect", [event["stage"]
                                           for event in result["phase_timings"]])

    def test_caller_composition_keeps_unknown_effect_as_incomplete(self):
        result, receipt = self._run_through_caller([
            self._predicates(value=False),
            self._predicates(value="unknown"),
        ], expect_submit=False)

        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "effect_unavailable")
        self.assertEqual(result["delivery"], "confirmed_partial")
        self.assertEqual(result["execution_progress"], {
            "status": "safe_yield", "reason": "effect_unavailable",
            "completed_actions": 1})
        self.assertEqual(receipt[0]["outcome"], "SAFE_YIELD")
        self.assertEqual(receipt[0]["completed_transitions"], 1)
        self.assertEqual(receipt[0]["reason"], "effect_unavailable")
        self.assertNotIn("verify_effect", [event["stage"]
                                           for event in result["phase_timings"]])

    def _run_through_caller(self, predicate_rows, refuse=None,
                            expect_submit=True):
        interface = compile_form_method(
            interface_id="caller-composition-interface-v1",
            session_scope="caller-composition-session-v1", surface="form",
            field_handle="field", submit_handle="submit",
            method_contract=EXPECTED_METHOD_CONTRACT)
        rows = iter(predicate_rows)
        executed = []
        receipts = []
        sequence = 0

        def observe(_payload):
            nonlocal sequence
            sequence += 1
            return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                    "surface": "form", "predicates": next(rows),
                    "evidence_ref": f"caller-frame-{sequence}",
                    "evidence_digest": f"caller-digest-{sequence}"}

        def admit(payload):
            if payload["operation"] == refuse:
                return {"eligible": False, "status": "missing",
                        "authorization": None,
                        "expected_sequence": payload["observation"]["sequence"],
                        "valid_until_ns": 0}
            return {"eligible": True, "status": "revalidated",
                    "authorization": "one-use",
                    "expected_sequence": payload["observation"]["sequence"],
                    "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}

        def execute(payload):
            executed.append(payload)
            return {"status": "completed", "action_id": f"caller-action-{len(executed)}",
                    "effect_ref": f"caller-effect-{len(executed)}",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}

        caller_adapters = {
            "observe_source": lambda _payload: {"source": "frame-0"},
            "acquire_anchor": lambda _payload: {"anchor": "frame-0"},
            "anchor_model": lambda _payload: {
                "call_id": "anchor-call",
                "output": {"status": "target_reference", "target": {"id": "form"}},
                "usage": {"input_tokens": 12, "output_tokens": 3},
                "requested_model": "offline-contract-model",
                "requested_effort": "medium", "cost": None},
            "final_revalidate": lambda _payload: {"status": "revalidated"},
            "verify_effect": lambda _payload: {
                "status": "succeeded", "evidence_ref": "independent-effect"},
        }
        spec = {"target": "submit exact task token", "route": "cold",
                "coarse_origin": "caller_provided",
                "provided_coarse": {"source": "frame-0"},
                "cached_target": None, "repair_on": [], "session_id": "test"}
        result = run_compiled_interface_in_caller(
            spec, caller_adapters, interface,
            {"observe": observe, "admit": admit, "execute": execute,
             "verify_effect": lambda payload: {
                 "status": "succeeded",
                 "evidence_ref": payload["observation"]["evidence_ref"]},
             "cancelled": lambda: False}, on_receipt=receipts.append,
            id_factory=lambda: "caller-attempt")
        self.assertEqual([row["operation"] for row in executed],
                         ["enter_exact_token", "activate_submit"]
                         if expect_submit and not refuse else
                         ["enter_exact_token"])
        return result, receipts

    def _run(self, predicate_rows, refuse=None):
        interface = compile_form_method(
            interface_id="composition-interface-v1",
            session_scope="composition-session-v1", surface="form",
            field_handle="field", submit_handle="submit",
            method_contract=EXPECTED_METHOD_CONTRACT)
        rows = iter(predicate_rows)
        self.executed = []
        admissions = []

        def observe(_payload):
            row = next(rows)
            sequence = getattr(observe, "sequence", 0) + 1
            observe.sequence = sequence
            return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                    "surface": "form", "predicates": row,
                    "evidence_ref": f"frame-{sequence}",
                    "evidence_digest": f"digest-{sequence}"}

        def admit(payload):
            operation = payload["operation"]
            admissions.append(operation)
            if operation == refuse:
                return {"eligible": False, "status": "missing", "authorization": None,
                        "expected_sequence": payload["observation"]["sequence"],
                        "valid_until_ns": 0}
            return {"eligible": True, "status": "revalidated", "authorization": "one-use",
                    "expected_sequence": payload["observation"]["sequence"],
                    "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}

        def execute(payload):
            self.executed.append(payload)
            return {"status": "completed", "action_id": f"action-{len(self.executed)}",
                    "effect_ref": f"effect-{len(self.executed)}",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}

        adapters = {
            "observe": observe,
            "admit": admit,
            "execute": execute,
            "verify_effect": lambda payload: {
                "status": "succeeded",
                "evidence_ref": payload["observation"]["evidence_ref"]},
            "cancelled": lambda: False,
        }
        return execute_compiled_interface(interface, adapters)

    @staticmethod
    def _predicates(*, value, submitted=False):
        return {"field_pixels_changed": bool(value),
                "field_value_matches_task": value,
                "field_target_present": True,
                "submit_target_present": True,
                "submission_pixels_changed": submitted}


if __name__ == "__main__":
    unittest.main()
