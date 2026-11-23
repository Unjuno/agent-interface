"""Direct contracts for the v3 caller / compiled GUI composition."""

import time
import unittest

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT, compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)


class CompiledExecutionV2CompositionTests(unittest.TestCase):
    def test_selected_target_builds_interface_and_receipt_failure_keeps_progress(self):
        interface = compile_form_method(
            interface_id="selected-interface-v2", session_scope="session-v2",
            surface="form", field_handle="field", submit_handle="submit",
            method_contract=EXPECTED_METHOD_CONTRACT)
        observations = iter([
            {"field_pixels_changed": False, "field_value_matches_task": False,
             "field_target_present": True, "submit_target_present": True,
             "submission_pixels_changed": False},
            {"field_pixels_changed": True, "field_value_matches_task": True,
             "field_target_present": True, "submit_target_present": True,
             "submission_pixels_changed": False},
            {"field_pixels_changed": True, "field_value_matches_task": True,
             "field_target_present": True, "submit_target_present": True,
             "submission_pixels_changed": True},
        ])
        operations = []

        def observe(_payload):
            sequence = getattr(observe, "sequence", 0) + 1
            observe.sequence = sequence
            return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                    "surface": "form", "predicates": next(observations),
                    "evidence_ref": f"frame-{sequence}",
                    "evidence_digest": f"digest-{sequence}"}

        def admit(payload):
            return {"eligible": True, "status": "revalidated",
                    "authorization": "one-use",
                    "expected_sequence": payload["observation"]["sequence"],
                    "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}

        def execute(payload):
            operations.append(payload["operation"])
            return {"status": "completed", "action_id": "action-1",
                    "effect_ref": "effect-1",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}

        caller_adapters = {
            "observe_source": lambda _p: {"source": "initial-capture"},
            "acquire_anchor": lambda _p: {"anchor": "capture"},
            "anchor_model": lambda _p: {
                "call_id": "model-call-1", "output": {"status": "target_reference",
                                                           "target": {"id": "coarse"}},
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "requested_model": "test-model", "requested_effort": "low",
                "cost": None, "visible_images_submitted": 1, "wait_ns": 5},
            "final_revalidate": lambda _p: {
                "status": "revalidated", "target": {"id": "fresh-selected"}},
            "verify_effect": lambda _p: {"status": "succeeded",
                                         "evidence_ref": "independent-post-score"},
        }
        spec = {"target": "submit exact token", "route": "cold",
                "coarse_origin": "caller_provided",
                "provided_coarse": {"source": "initial-capture"},
                "cached_target": None, "local_repair_on": [], "repair_on": [],
                "session_id": "session-v2"}
        built_from = []
        retained = []

        result = run_compiled_interface_in_caller(
            spec, caller_adapters,
            lambda selected: built_from.append(selected["target"]) or interface,
            {"observe": observe, "admit": admit, "execute": execute,
             "verify_effect": lambda _p: {"status": "succeeded",
                                          "evidence_ref": "compiled-effect"},
             "cancelled": lambda: False},
            on_receipt=lambda _receipt: (_ for _ in ()).throw(OSError("sink unavailable")),
            id_factory=lambda: "attempt-v2")

        self.assertEqual(built_from, [{"id": "fresh-selected"}])
        self.assertEqual(operations, ["enter_exact_token", "activate_submit"])
        self.assertEqual(result["outcome"], "CALLER_FAILED")
        self.assertEqual(result["delivery"], "confirmed")
        self.assertEqual(result["execution_progress"], {
            "status": "completed"})
        receipt = result["compiled_execution_receipt"]
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)
        self.assertTrue(receipt["transitions"][0]["release_verified"])
        self.assertEqual(result["compiled_receipt_publication_error"]["type"], "OSError")


if __name__ == "__main__":
    unittest.main()


