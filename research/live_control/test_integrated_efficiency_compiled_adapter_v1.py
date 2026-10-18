"""Contract tests for the #57 six-task compiled form adapter."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("integrated_efficiency_compiled_adapter_v1.py")


def load_module():
    if not MODULE_PATH.is_file():
        raise AssertionError("candidate adapter module must exist")
    spec = importlib.util.spec_from_file_location("compiled_adapter_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("candidate adapter module must be importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompiledFormAdapterTests(unittest.TestCase):
    def test_compiles_checked_handles_and_effect_gated_two_step_method(self):
        adapter = load_module()
        method_contract = {
            "first_action": "enter_exact_token",
            "continue_when": "field_pixels_changed_and_submit_revalidated",
            "second_action": "activate_submit",
            "complete_when": "submission_pixels_changed_then_independent_score",
        }
        interface = adapter.compile_form_method(
            interface_id="test-interface-v1", session_scope="test-session-v1",
            surface="form", field_handle="task_field", submit_handle="task_submit",
            method_contract=method_contract)

        self.assertEqual(interface["symbols"]["value_field"]["target_reference"], "task_field")
        self.assertEqual(interface["symbols"]["submit_control"]["target_reference"], "task_submit")
        self.assertEqual(interface["actions"]["enter_token"]["expected_effect"],
                         {"field_pixels_changed": True})
        self.assertEqual(interface["method"]["states"]["filled"]["branches"][0], {
            "when": {"field_pixels_changed": True, "submit_target_present": True},
            "outcome": "action", "action": "submit_form", "next_state": "submitted",
            "reason": None,
        })
        self.assertEqual(interface["method"]["states"]["submitted"]["branches"][0]["outcome"],
                         "complete")

    def test_rejects_model_method_that_skips_observed_intermediate_effect(self):
        adapter = load_module()
        method_contract = {
            "first_action": "enter_exact_token",
            "continue_when": "immediately_submit",
            "second_action": "activate_submit",
            "complete_when": "submission_pixels_changed_then_independent_score",
        }
        with self.assertRaises(ValueError):
            adapter.compile_form_method(
                interface_id="test-interface-v1", session_scope="test-session-v1",
                surface="form", field_handle="task_field", submit_handle="task_submit",
                method_contract=method_contract)


if __name__ == "__main__":
    unittest.main()
