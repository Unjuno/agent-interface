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

    def test_terminal_before_cancel_is_rejected_by_candidate_and_independent_audit(self):
        events = copy.deepcopy(self.events)
        cancel = next(row for row in events if row.get("event") == "cancel_requested"
                      and row.get("id") == "cover-0")
        terminal = next(row for row in events if row.get("event") == "terminal"
                        and row.get("id") == "cover-0")
        # This cancellation has no interruption receipt, so it exercises the
        # terminal-release chronology gate directly.
        interruption = terminal.get("interruption") or {}
        self.assertIsNone(interruption.get("record"))
        terminal["release"]["verified_ns"] = cancel["requested_ns"] - 3
        terminal["terminal_ns"] = cancel["requested_ns"] - 2
        cancel["requested_ns"] += 10
        with self.assertRaisesRegex(ValueError, "not verified empty"):
            analyze(events, self.owner, self.report, self.prior)
        result = analyze(self.events, self.owner, self.report, self.prior)
        with self.assertRaisesRegex(ValueError, "source terminal release invalid"):
            validate(result, events, self.owner, self.report)

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

    def test_unverified_release_event_does_not_count_as_verified_coverage(self):
        events = copy.deepcopy(self.events)
        row = next(row for row in events if row.get("event") == "input_released")
        row["event"] = "input_release_unverified"
        result = analyze(events, self.owner, self.report, self.prior)
        self.assertEqual(result["active_interruption_coverage"],
                         {"numerator": 0, "denominator": 3})
        self.assertEqual(result["input_release_event_rows"], 0)
        self.assertEqual(result["input_release_unverified_event_rows"], 1)
        self.assertTrue(validate(result, events, self.owner, self.report))

    def test_duplicate_cancel_id_is_rejected(self):
        events = copy.deepcopy(self.events)
        cancel_indices = [i for i, row in enumerate(events)
                          if row.get("event") == "cancel_requested"]
        events[cancel_indices[-1]] = copy.deepcopy(events[cancel_indices[0]])
        with self.assertRaisesRegex(ValueError, "cancel_requested event IDs"):
            analyze(events, self.owner, self.report, self.prior)

    def test_duplicate_release_id_is_rejected(self):
        events = copy.deepcopy(self.events)
        release = next(row for row in events if row.get("event") == "input_released")
        events.append(copy.deepcopy(release))
        with self.assertRaisesRegex(ValueError, "release event IDs"):
            analyze(events, self.owner, self.report, self.prior)

    def test_release_event_without_terminal_is_rejected(self):
        events = copy.deepcopy(self.events)
        release = next(row for row in events if row.get("event") == "input_released")
        release["id"] = "unknown-program"
        with self.assertRaisesRegex(ValueError, "without a terminal"):
            analyze(events, self.owner, self.report, self.prior)


if __name__ == "__main__":
    unittest.main(verbosity=2)
