from __future__ import annotations

import threading
import unittest

from input_boundary import KeyStateSampler, audit_expiry_key_release


DEADLINE = 1_000_000_000
QPC = 10_000_000_000


def row(lease_before, lease_after, qpc_start, qpc_end, down):
    return {"monotonic_before_ns": lease_before,
        "monotonic_after_ns": lease_after,
        "perf_counter_start_ns": qpc_start,
        "perf_counter_end_ns": qpc_end,
        "w_key_down": down, "error_type": None}


class InputBoundaryTests(unittest.TestCase):
    def test_verifies_tightly_bracketed_down_to_up_across_coarse_tick(self):
        result = audit_expiry_key_release([
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC, QPC + 1_000, True),
            row(DEADLINE, DEADLINE, QPC + 11_001_000,
                QPC + 11_002_000, False)], DEADLINE)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["qpc_bracket_gap_ns"], 11_000_000)

    def test_rejects_wide_precise_bracket(self):
        result = audit_expiry_key_release([
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC, QPC + 1_000, True),
            row(DEADLINE, DEADLINE, QPC + 24_001_000,
                QPC + 24_002_000, False)], DEADLINE)
        self.assertEqual(result["status"], "not_verified")

    def test_r144_read_durations_cannot_turn_outer_overrun_into_pass(self):
        # R144's inner gap was 19.9903 ms, but the observations only bound
        # the transition to a 20.0044 ms interval including both reads.
        result = audit_expiry_key_release([
            row(DEADLINE - 545_000, DEADLINE - 535_100,
                QPC, QPC + 9_700, True),
            row(DEADLINE + 19_455_000, DEADLINE + 19_459_600,
                QPC + 20_000_000, QPC + 20_004_400, False)], DEADLINE)
        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(result["qpc_bracket_gap_ns"], 19_990_300)
        self.assertEqual(result["qpc_bracket_outer_ns"], 20_004_400)

    def test_limit_applies_to_outer_endpoints_inclusively(self):
        for end_ns, expected in ((20_000_000, "verified"),
                                 (20_000_001, "not_verified")):
            with self.subTest(end_ns=end_ns):
                result = audit_expiry_key_release([
                    row(DEADLINE - 10_000, DEADLINE - 1_000,
                        QPC, QPC + 7_000, True),
                    row(DEADLINE, DEADLINE + 10_000,
                        QPC + 19_995_000, QPC + end_ns, False)], DEADLINE)
                self.assertEqual(result["status"], expected)

    def test_post_deadline_down_is_measured_until_first_up(self):
        result = audit_expiry_key_release([
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC, QPC + 1_000, True),
            row(DEADLINE, DEADLINE, QPC + 2_000_000,
                QPC + 2_001_000, True),
            row(DEADLINE + 15_625_000, DEADLINE + 15_625_000,
                QPC + 12_000_000, QPC + 12_001_000, False)], DEADLINE)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["qpc_bracket_gap_ns"], 11_999_000)
        self.assertEqual(result["post_deadline_down_duration_ns"],
                         10_000_000)
        self.assertTrue(result["first_sample_fully_after_deadline"][
            "w_key_down"])
        self.assertFalse(result["first_up_read_fully_after_deadline"][
            "w_key_down"])

    def test_r104_shape_uses_first_up_and_stays_over_20ms(self):
        result = audit_expiry_key_release([
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC, QPC + 8_800, True),
            row(DEADLINE, DEADLINE, QPC + 1_991_200,
                QPC + 2_000_000, True),
            row(DEADLINE + 15_625_000, DEADLINE + 15_625_000,
                QPC + 22_000_000, QPC + 22_008_800, False)], DEADLINE)
        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(result["qpc_bracket_gap_ns"], 21_991_200)
        self.assertEqual(result["post_deadline_down_duration_ns"],
                         20_008_800)

    def test_rejects_missing_down_or_post_deadline_up(self):
        cases = [
            [row(DEADLINE - 1, DEADLINE - 1, QPC, QPC + 10, False),
             row(DEADLINE, DEADLINE, QPC + 20, QPC + 30, False)],
            [row(DEADLINE - 1, DEADLINE - 1, QPC, QPC + 10, True)],
        ]
        for samples in cases:
            with self.subTest(samples=samples):
                self.assertEqual(audit_expiry_key_release(samples, DEADLINE)[
                    "status"], "not_verified")

    def test_allows_coarse_monotonic_duplicates_but_rejects_bad_qpc_order(self):
        samples = [
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC, QPC + 10, True),
            row(DEADLINE - 15_625_000, DEADLINE - 15_625_000,
                QPC + 20, QPC + 30, True),
            row(DEADLINE, DEADLINE, QPC + 40, QPC + 50, False),
        ]
        result = audit_expiry_key_release(samples, DEADLINE)
        self.assertEqual(result["status"], "verified")
        samples[1]["perf_counter_start_ns"] = QPC
        self.assertEqual(audit_expiry_key_release(samples, DEADLINE)[
            "status"], "not_verified")

    def test_rejects_unknown_state_and_missing_dual_clock_fields(self):
        samples = [
            row(DEADLINE - 1, DEADLINE - 1, QPC, QPC + 10, None),
            row(DEADLINE, DEADLINE, QPC + 20, QPC + 30, False),
        ]
        self.assertEqual(audit_expiry_key_release(samples, DEADLINE)[
            "status"], "not_verified")
        self.assertTrue(audit_expiry_key_release(samples, DEADLINE)[
            "malformed_samples"] is False)
        self.assertEqual(audit_expiry_key_release([
            {"monotonic_ns": DEADLINE - 1, "w_key_down": True},
            {"monotonic_ns": DEADLINE + 1, "w_key_down": False}], DEADLINE)[
                "status"], "not_verified")

    def test_sampler_records_bounded_samples_and_reader_failure(self):
        reached = threading.Event()
        def reader():
            reached.set()
            return True
        sampler = KeyStateSampler(reader, interval_ns=1_000_000,
            max_samples=2).start()
        self.assertTrue(reached.wait(1))
        result = sampler.stop(join_timeout_s=1)
        self.assertLessEqual(result["sample_count"], 2)
        self.assertEqual(result["clock"], "time.perf_counter_ns")
        self.assertEqual(result["lease_clock"], "time.monotonic_ns")

        reached.clear()
        failed = KeyStateSampler(lambda: (reached.set() or 1),
            interval_ns=1_000_000).start()
        self.assertTrue(reached.wait(1))
        failure = failed.stop(join_timeout_s=1)
        self.assertEqual(failure["read_error_type"], "ValueError")
        self.assertIsNone(failure["samples"][0]["w_key_down"])


if __name__ == "__main__":
    unittest.main()
