import copy
import unittest

from comparison_measurement_v1 import validate_measured_run, validate_reuse_horizon
import test_comparison_measurement_v1 as comparison_tests
import test_effect_receipt_handoff_v1 as effect_tests


class EffectReceiptReuseHorizonIntegrationTests(unittest.TestCase):
    def compose(self, interval):
        fixture = effect_tests.EffectReceiptHandoffTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        fixture.measured["task_ledger"]["task"]["task_id"] = "task-01"
        fixture.receipt["task_id"] = "task-01"
        fixture.receipt["effect_interval_ns"] = interval
        fixture.write_receipt()
        adapted = fixture.adapt()["measured_run"]
        value = comparison_tests.ComparisonMeasurementTests.horizon()
        c_run = value["blocks"][0]["runs"][2]
        c_run.update(copy.deepcopy(adapted))
        ledger = c_run["task_ledger"]
        ledger["comparison"] = {
            "arm": "C", "block": 1, "order": 3, "task_seed": "seed-01"
        }
        ledger["task"] = {
            "task_id": "task-01", "fixture_sha256": "a" * 64,
            "scorer_sha256": "b" * 64,
        }
        ledger["source"] = {"commit": "c" * 40, "route_sha256": "f" * 64}
        ledger["environment_sha256"] = "9" * 64
        ledger["model"] = {
            "id": "model-x", "effort": "low", "request_config_sha256": "8" * 64
        }
        ledger["run_id"] = "run-C"
        for event in ledger["events"]:
            if event.get("attempt_id") == "attempt-1":
                event["attempt_id"] = "model-C-1"
            if event.get("model_attempt_id") == "attempt-1":
                event["model_attempt_id"] = "model-C-1"
        for image in c_run["measurement"]["model_delivered_images"]:
            if image["attempt_id"] == "attempt-1":
                image["attempt_id"] = "model-C-1"
        value["c_plan_trace"][0]["plan_generation_attempt_ids"] = ["model-C-1"]
        value["c_plan_trace"][0]["attempt_dispositions"][0]["attempt_id"] = "model-C-1"
        return value, c_run

    def test_timely_receipt_qualifies_integrated_horizon_break_even(self):
        value, c_run = self.compose({"lower_ns": 144, "upper_ns": 145})
        self.assertTrue(validate_measured_run(c_run)["task_success"])
        result = validate_reuse_horizon(value)
        self.assertEqual(result["token_break_even_task_index"], {"A": 2, "B": 2})
        self.assertEqual(
            result["correctness_qualified_token_break_even_task_index"],
            {"A": 2, "B": 2},
        )

    def test_post_horizon_receipt_preserves_fact_but_blocks_qualified_break_even(self):
        value, c_run = self.compose({"lower_ns": 161, "upper_ns": 165})
        measured = validate_measured_run(c_run)
        self.assertTrue(measured["factual_task_success"])
        self.assertFalse(measured["task_success"])
        result = validate_reuse_horizon(value)
        self.assertEqual(result["token_break_even_task_index"], {"A": 2, "B": 2})
        self.assertEqual(
            result["correctness_qualified_token_break_even_task_index"],
            {"A": None, "B": None},
        )

    def test_unknown_receipt_time_preserves_fact_but_blocks_qualified_break_even(self):
        value, c_run = self.compose(None)
        measured = validate_measured_run(c_run)
        self.assertTrue(measured["factual_task_success"])
        self.assertIsNone(measured["task_success"])
        result = validate_reuse_horizon(value)
        self.assertEqual(result["token_break_even_task_index"], {"A": 2, "B": 2})
        self.assertEqual(
            result["correctness_qualified_token_break_even_task_index"],
            {"A": None, "B": None},
        )


if __name__ == "__main__":
    unittest.main()
