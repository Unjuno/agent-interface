"""Literal clock/counter regressions before instrumented native collection."""
import unittest
import timing

class TimingTests(unittest.TestCase):
    def test_records_overslept_coarse_wake_without_inventing_spin(self):
        ticks = iter([0, 117_000_000])
        calls = []
        r = timing.paced_wait(100_000_000, lambda: next(ticks), calls.append)
        self.assertEqual(r, {"begin_ns": 0, "return_ns": 117_000_000, "spin_enter_ns": None,
                            "sleeps": [{"start_ns": 0, "return_ns": 117_000_000, "requested_ns": 85_000_000}]})
        self.assertEqual(calls, [0.085])

    def test_records_coarse_and_spin_without_late_return(self):
        ticks = iter([0, 86_000_000, 99_000_000, 100_000_000])
        r = timing.paced_wait(100_000_000, lambda: next(ticks), lambda seconds: None)
        self.assertEqual(r["return_ns"], 100_000_000)
        self.assertEqual(r["spin_enter_ns"], 86_000_000)
        self.assertEqual(r["sleeps"][0]["requested_ns"], 85_000_000)

    def test_already_late_call_is_distinct_from_sleep_overshoot(self):
        r = timing.paced_wait(100, lambda: 117, lambda seconds: self.fail("no sleep permitted"))
        self.assertEqual(r, {"begin_ns": 117, "return_ns": 117, "spin_enter_ns": None, "sleeps": []})

    def test_counter_values_are_parsed_as_integers(self):
        self.assertEqual(timing.parse_cpu("usage_usec 10\nnr_periods 2\nnr_throttled 0\nthrottled_usec 0\n"),
                         {"usage_usec": 10, "nr_periods": 2, "nr_throttled": 0, "throttled_usec": 0})
    def test_duplicate_negative_and_noninteger_counters_are_refused(self):
        for raw in ("usage_usec 1\nusage_usec 2\n", "usage_usec -1\n", "usage_usec nan\n", "bad too many fields\n"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    timing.parse_cpu(raw)

if __name__ == "__main__":
    unittest.main()
