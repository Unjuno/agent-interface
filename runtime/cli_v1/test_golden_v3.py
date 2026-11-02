from __future__ import annotations
import unittest
from unittest import mock
from runtime.cli_v1.golden_v3 import adapt_dispatch_result,dispatch_golden_v3

class GoldenV3AdapterTests(unittest.TestCase):
    def test_returned_requires_both_task_and_program_success(self):
        row=adapt_dispatch_result({"status":"returned","result":{"program_completed":True,"task_success":True,"partial_effects":[]}},usage={"input":3},lifecycle=["dispatch","effect","release","cleanup"])
        self.assertEqual(row["status"],"success"); self.assertEqual(row["usage"],{"input":3}); self.assertEqual(row["usage_status"],"reported"); self.assertFalse(row["authority_granted"])

    def test_missing_usage_is_unavailable_not_an_empty_zero_record(self):
        row=adapt_dispatch_result({"status":"returned","result":{"program_completed":True}})
        self.assertEqual(row["usage"],{})
        self.assertEqual(row["usage_status"],"unavailable")

    def test_dispatch_usage_is_reported_when_present(self):
        row=adapt_dispatch_result({"status":"returned","usage":{"input_tokens":0,"output_tokens":0}})
        self.assertEqual(row["usage"],{"input_tokens":0,"output_tokens":0})
        self.assertEqual(row["usage_status"],"reported")

    def test_partial_token_usage_is_not_reported_as_complete(self):
        partial_usages = (
            {"input_tokens":12},
            {"output_tokens":4},
            {"cached_input_tokens":3},
            {"reasoning_tokens":1},
            {"input_tokens":12,"cached_input_tokens":3},
            {"output_tokens":4,"reasoning_tokens":1},
        )
        for usage in partial_usages:
            with self.subTest(usage=usage):
                row=adapt_dispatch_result({"status":"runtime_failed","usage":usage})
                self.assertEqual(row["status"],"partial")
                self.assertEqual(row["usage"],usage)
                self.assertEqual(row["usage_status"],"partial")

    def test_complete_token_usage_survives_failed_dispatch(self):
        usage={"input_tokens":12,"output_tokens":4,"cached_input_tokens":3,"reasoning_tokens":1}
        row=adapt_dispatch_result({"status":"runtime_failed","usage":usage})
        self.assertEqual(row["status"],"partial")
        self.assertEqual(row["usage"],usage)
        self.assertEqual(row["usage_status"],"reported")

    def test_malformed_token_usage_is_not_reported(self):
        for usage in ({"input_tokens":True,"output_tokens":4},
                      {"input_tokens":12,"output_tokens":-1},
                      {"input_tokens":12,"output_tokens":4,"cached_input_tokens":None}):
            with self.subTest(usage=usage):
                self.assertEqual(adapt_dispatch_result({"status":"returned","usage":usage})["usage_status"],"malformed")
    def test_effect_success_without_task_success_is_partial(self):
        row=adapt_dispatch_result({"status":"returned","result":{"program_completed":True,"task_success":False,"partial_effects":["save"]}})
        self.assertEqual(row["status"],"partial"); self.assertEqual(row["partial_effects"],["save"])
        self.assertTrue(row["program_completed"])
        self.assertFalse(row["task_success"])
    def test_refusal_and_diagnostic(self):
        row=adapt_dispatch_result({"status":"backend_unavailable","error":"NO_BACKEND"},lifecycle=["doctor","refusal"])
        self.assertEqual(row["status"],"refused"); self.assertEqual(row["diagnostic"],"NO_BACKEND")
    def test_cleanup_failure_cannot_succeed(self):
        row=adapt_dispatch_result({"status":"returned","result":{"program_completed":True,"task_success":True},"cleanup_error":"close"})
        self.assertEqual(row["status"],"cleanup_failed")
        self.assertTrue(row["program_completed"])
        self.assertFalse(row["task_success"])
        self.assertTrue(row["raw_dispatch"]["result"]["task_success"])
    def test_unknown_inputs_fail_closed(self):
        rejected=adapt_dispatch_result({"status":"mystery"})
        self.assertEqual(rejected["adapter_error"],"UNKNOWN_STATUS")
        self.assertEqual(rejected["usage_status"],"unavailable")
        self.assertEqual(adapt_dispatch_result({"status":"returned"},lifecycle=["bogus"])["adapter_error"],"UNKNOWN_LIFECYCLE")
    def test_public_wrapper_preserves_dispatch_boundary(self):
        raw={"status":"returned","result":{"program_completed":True,"task_success":True}}
        with mock.patch("runtime.cli_v1.golden_v3.dispatch",return_value=raw) as call:
            row=dispatch_golden_v3({"p":1},{"fixture":1},current_observation_seq=2,current_binding_revision=4,usage={"input":1})
        call.assert_called_once_with({"p":1},{"fixture":1},current_observation_seq=2,current_binding_revision=4,display_name=None)
        self.assertEqual(row["status"],"success"); self.assertEqual(row["usage"],{"input":1})

    def test_ambiguous_delivery_never_maps_to_success(self):
        for delivery in ("ambiguous", "uncertain", "write_uncertain", "delivery_uncertain"):
            row = adapt_dispatch_result({
                "status": "returned",
                "delivery": delivery,
                "result": {"program_completed": True, "task_success": True},
            })
            self.assertEqual(row["status"], "refused", delivery)
            self.assertFalse(row["program_completed"], delivery)
            self.assertFalse(row["task_success"], delivery)
            self.assertIn("AMBIGUOUS_DELIVERY", row["diagnostic"])

    def test_nested_ambiguous_delivery_never_maps_to_success(self):
        row = adapt_dispatch_result({
            "status": "returned",
            "result": {
                "delivery": "ambiguous",
                "program_completed": True,
                "task_success": True,
                "partial_effects": ["attempted"],
            },
        })
        self.assertEqual(row["status"], "refused")
        self.assertFalse(row["program_completed"])
        self.assertFalse(row["task_success"])
        self.assertEqual(row["partial_effects"], ["attempted"])
        self.assertIn("AMBIGUOUS_DELIVERY", row["diagnostic"])

if __name__=="__main__": unittest.main()
