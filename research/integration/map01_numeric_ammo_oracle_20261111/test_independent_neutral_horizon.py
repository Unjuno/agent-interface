import unittest

from independent_neutral_horizon import observe_neutral_horizon


class FakeClock:
    def __init__(self):
        self.now = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += round(seconds * 1_000_000_000)


class IndependentNeutralHorizonTests(unittest.TestCase):
    def run_observation(self, states, *, generation="generation-a",
                        expected_generation="generation-a", gap_ns=10_000_000):
        clock = FakeClock()
        iterator = iter(states)

        def read_state():
            try:
                return next(iterator)
            except StopIteration:
                return {"LEFT_BUTTON_down": False, "W_key_down": False}

        def clock_with_sample_step():
            value = clock.clock()
            # Make each input read bracket one nanosecond while retaining the
            # fake sleep clock's regular sample interval.
            return value

        return observe_neutral_horizon(
            read_input_state=read_state,
            read_identity=lambda: "owned-process",
            read_generation=lambda: generation,
            expected_identity="owned-process",
            expected_generation=expected_generation,
            horizon_ns=100_000_000,
            max_sample_gap_ns=gap_ns,
            max_read_bracket_ns=20_000_000,
            total_budget_ns=300_000_000,
            clock_ns=clock_with_sample_step,
            sleep_ns=clock.sleep,
        )

    def test_continuously_neutral_state_verifies_full_horizon(self):
        report = self.run_observation([])
        self.assertEqual(report["status"], "VERIFIED")
        self.assertGreaterEqual(report["samples"][-1]["after_ns"]
                                - report["neutral_since_ns"], 100_000_000)

    def test_down_sample_restarts_neutral_interval(self):
        report = self.run_observation([
            {"LEFT_BUTTON_down": False, "W_key_down": False},
            {"LEFT_BUTTON_down": False, "W_key_down": True},
        ])
        self.assertEqual(report["status"], "VERIFIED")
        self.assertGreaterEqual(report["sample_count"], 13)

    def test_generation_change_fails_closed(self):
        report = self.run_observation([], generation="generation-b")
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["reason"], "initial_identity_or_generation_mismatch")

    def test_sample_gap_over_limit_fails_closed(self):
        clock = FakeClock()
        sleeps = 0

        def irregular_sleep(_seconds):
            nonlocal sleeps
            sleeps += 1
            clock.now += 120_000_000 if sleeps == 1 else 10_000_000

        report = observe_neutral_horizon(
            read_input_state=lambda: {"LEFT_BUTTON_down": False,
                                      "W_key_down": False},
            read_identity=lambda: "owned-process",
            read_generation=lambda: "generation-a",
            expected_identity="owned-process", expected_generation="generation-a",
            horizon_ns=100_000_000, max_sample_gap_ns=50_000_000,
            total_budget_ns=300_000_000,
            clock_ns=clock.clock, sleep_ns=irregular_sleep)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["reason"], "sample_gap_exceeded")

    def test_generation_change_during_horizon_fails_closed(self):
        clock = FakeClock()
        generations = iter(["generation-a", "generation-a", "generation-b"])
        report = observe_neutral_horizon(
            read_input_state=lambda: {"LEFT_BUTTON_down": False,
                                      "W_key_down": False},
            read_identity=lambda: "owned-process",
            read_generation=lambda: next(generations),
            expected_identity="owned-process", expected_generation="generation-a",
            horizon_ns=100_000_000, total_budget_ns=300_000_000,
            clock_ns=clock.clock, sleep_ns=clock.sleep)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["reason"], "identity_or_generation_changed_during_horizon")


if __name__ == "__main__":
    unittest.main()
