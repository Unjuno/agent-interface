"""Regression tests for the exact-value-gated compiled form adapter v2."""

import unittest
import time

from research.live_control import integrated_efficiency_compiled_adapter_v2 as adapter
from runtime.core_v1.compiled_gui import run as run_compiled


METHOD = {
    "first_action": "enter_exact_token",
    "continue_when": "exact_task_value_observed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}


class CompiledFormAdapterV2Tests(unittest.TestCase):
    def test_submit_branch_requires_exact_task_value_and_submit_target(self):
        interface = adapter.compile_form_method(
            interface_id="test-interface-v2", session_scope="test-session-v2",
            surface="form", field_handle="task_field", submit_handle="task_submit",
            method_contract=METHOD)
        self.assertEqual(interface["method"]["states"]["verify_value"]["branches"][0]["when"], {
            "field_value_matches_task": True, "submit_target_present": True,
        })
        self.assertIn("field_value_matches_task", interface["predicates"])
        self.assertEqual(interface["method"]["version"], "2")

    def test_pixel_change_with_wrong_value_safe_yields_without_submit(self):
        receipt, actions = self._execute([
            {"field_pixels_changed": False, "field_value_matches_task": False,
             "field_target_present": True,
             "submit_target_present": True, "submission_pixels_changed": False},
            {"field_pixels_changed": True, "field_value_matches_task": False,
             "field_target_present": True,
             "submit_target_present": True, "submission_pixels_changed": False},
        ])
        self.assertEqual(receipt["outcome"], "SAFE_YIELD")
        self.assertEqual(receipt["reason"], "effect_failed")
        self.assertEqual(actions, ["enter_exact_token"])

    def test_exact_task_value_allows_submit_then_independent_completion(self):
        receipt, actions = self._execute([
            {"field_pixels_changed": False, "field_value_matches_task": False,
             "field_target_present": True,
             "submit_target_present": True, "submission_pixels_changed": False},
            {"field_pixels_changed": True, "field_value_matches_task": True,
             "field_target_present": True,
             "submit_target_present": True, "submission_pixels_changed": False},
            {"field_pixels_changed": True, "field_value_matches_task": True,
             "field_target_present": True,
             "submit_target_present": True, "submission_pixels_changed": True},
        ])
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(actions, ["enter_exact_token", "activate_submit"])

    def _execute(self, predicate_rows):
        interface = adapter.compile_form_method(
            interface_id="test-interface-v2", session_scope="test-session-v2",
            surface="form", field_handle="task_field", submit_handle="task_submit",
            method_contract=METHOD)
        observations = iter(predicate_rows)
        actions = []

        def observe(_payload):
            predicates = next(observations)
            # Keep sequence strictly increasing across observation-only stops.
            sequence = getattr(observe, "sequence", 0) + 1
            observe.sequence = sequence
            return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                    "surface": "form", "predicates": predicates,
                    "evidence_ref": f"frame-{sequence}",
                    "evidence_digest": f"digest-{sequence}"}

        def execute(payload):
            actions.append(payload["operation"])
            return {"status": "completed", "action_id": f"action-{len(actions)}",
                    "effect_ref": f"effect-{len(actions)}",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}

        receipt = run_compiled(interface, {
            "observe": observe,
            "admit": lambda payload: {
                "eligible": True, "status": "revalidated", "authorization": "one-use",
                "expected_sequence": payload["observation"]["sequence"],
                "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
            },
            "execute": execute,
            "verify_effect": lambda payload: {
                "status": "succeeded", "evidence_ref": payload["observation"]["evidence_ref"]},
            "cancelled": lambda: False,
        })
        return receipt, actions

    def test_v1_pixel_change_method_is_not_accepted_as_v2(self):
        incompatible = dict(METHOD, continue_when="field_pixels_changed_and_submit_revalidated")
        with self.assertRaises(ValueError):
            adapter.compile_form_method(
                interface_id="test-interface-v2", session_scope="test-session-v2",
                surface="form", field_handle="task_field", submit_handle="task_submit",
                method_contract=incompatible)


if __name__ == "__main__":
    unittest.main()
