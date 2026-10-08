import copy
import unittest

from .audit_result import validate
from .run_audit import analyze, load_inputs


class RetainedReleaseTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events, cls.owner, cls.report, cls.prior = load_inputs()

    def test_retained_trace_reconciles_and_exposes_coverage_gap(self):
        result = analyze(self.events, self.owner, self.report, self.prior)
        self.assertEqual(result["cancel_requests"], 7)
        self.assertEqual(result["cancellations_with_prior_keys_held"], 4)
        self.assertEqual(result["active_interruption_coverage"],
                         {"numerator": 1, "denominator": 3})
        self.assertEqual(result["aggregate_cancel_to_owner_verified_ms"],
                         {"min": 0.771224, "max": 2.652407})
        self.assertFalse(result["owner_release_has_per_key_timestamps"])
        self.assertTrue(validate(result, self.events, self.owner, self.report))

    def test_terminal_release_corruption_is_rejected(self):
        events = copy.deepcopy(self.events)
        terminal = next(row for row in events if row.get("event") == "terminal" and
                        row.get("id") == "cover-1")
        terminal["release"]["keys_down"] = ["space"]
        with self.assertRaises(ValueError):
            analyze(events, self.owner, self.report, self.prior)

    def test_interruption_timestamp_after_terminal_is_rejected(self):
        events = copy.deepcopy(self.events)
        terminal = next(row for row in events if row.get("event") == "terminal" and
                        row.get("id") == "cover-1")
        terminal["interruption"]["record"]["verified_ns"] = terminal["terminal_ns"] + 1
        with self.assertRaises(ValueError):
            analyze(events, self.owner, self.report, self.prior)

    def test_coverage_result_mutation_is_rejected_by_independent_oracle(self):
        result = analyze(self.events, self.owner, self.report, self.prior)
        result["active_interruption_coverage"]["numerator"] = 3
        with self.assertRaises(ValueError):
            validate(result, self.events, self.owner, self.report)

    def test_release_latency_mutation_is_rejected_by_independent_oracle(self):
        result = analyze(self.events, self.owner, self.report, self.prior)
        result["active_interruption_rows"][0]["cancel_to_owner_verified_ms"] = 0.0
        with self.assertRaises(ValueError):
            validate(result, self.events, self.owner, self.report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
