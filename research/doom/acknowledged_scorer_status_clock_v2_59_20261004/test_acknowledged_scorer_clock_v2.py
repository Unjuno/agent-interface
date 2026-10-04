import unittest

from acknowledged_scorer_v1 import AcknowledgedSampler
from acknowledged_scorer_clock_v2 import AcknowledgedSamplerClockV2
from independent_progress_clock_v2 import ProgressSample


class Game:
    def __init__(self):
        self.tic = 7
        self.calls = 0
    def is_episode_finished(self):
        return False
    def get_episode_time(self):
        return self.tic
    def advance_action(self, count, update):
        self.calls += 1
        self.tic += 3


def sample(game, variables, timeout):
    return ProgressSample(100, 0, 0, False, False, False)


class ClockFailureTests(unittest.TestCase):
    def sampler(self, cls):
        calls = []
        rows = []
        def clock():
            calls.append(True)
            if len(calls) == 2:
                raise OSError("return clock unavailable")
            return 10
        return cls(sample, "clock-run", rows.append, clock_ns=clock), rows

    def run_return_clock_failure(self, cls):
        game = Game()
        sampler, rows = self.sampler(cls)
        with self.assertRaisesRegex(OSError, "return clock unavailable"):
            sampler(game, None, 10)
        self.assertEqual(game.calls, 1)
        return rows[0]

    def test_v1_reproduces_lost_return_fact(self):
        row = self.run_return_clock_failure(AcknowledgedSampler)
        self.assertEqual(row.get("update_status", row.get("status")), "UPDATE_UNAVAILABLE")
        self.assertNotIn("producer", row)

    def test_v2_keeps_api_return_separate_from_unavailable_metadata(self):
        row = self.run_return_clock_failure(AcknowledgedSamplerClockV2)
        self.assertEqual(row["status"], "UPDATE_METADATA_UNAVAILABLE")
        self.assertEqual(row["update_status"], "UPDATE_RETURNED")
        self.assertEqual(row["sample_status"], "NOT_ATTEMPTED")
        self.assertEqual(row["producer"]["observation_status"], "UPDATE_RETURNED_UNTIMED")
        self.assertEqual(row["producer"]["tic_before"], 7)
        self.assertNotIn("tic_after", row["producer"])
        self.assertNotIn("update_returned_ns", row["producer"])

    def test_no_clock_qualification_means_no_sample_or_retry(self):
        game = Game()
        samples = []
        rows = []
        def fail_sample(*args):
            samples.append(True)
            return sample(*args)
        sampler, _ = self.sampler(AcknowledgedSamplerClockV2)
        sampler.sample_fn = fail_sample
        sampler.emit = rows.append
        with self.assertRaises(OSError):
            sampler(game, None, 10)
        self.assertEqual(samples, [])
        with self.assertRaisesRegex(RuntimeError, "retry refused"):
            sampler(game, None, 10)
        self.assertEqual(game.calls, 1)

    def test_reuses_observed_external_ack_instead_of_taking_a_second_timestamp(self):
        rows = []
        clock_calls = []
        sampler = AcknowledgedSamplerClockV2(
            sample, "clock-run", rows.append,
            clock_ns=lambda: clock_calls.append(True) or 10)
        class ObservedGame(Game):
            def advance_action(self, count, update):
                super().advance_action(count, update)
                sampler.observe_external_update(self, 7, 10, 10, 20)
        game = ObservedGame()
        result = sampler(game, None, 10)
        self.assertEqual(clock_calls, [True])
        self.assertEqual(result.producer["update_returned_ns"], 20)
        self.assertEqual(rows[0]["update_status"], "UPDATE_RETURNED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
