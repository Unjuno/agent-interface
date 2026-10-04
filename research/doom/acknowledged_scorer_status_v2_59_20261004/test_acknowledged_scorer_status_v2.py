import unittest

from independent_progress_clock_v2 import ProgressSample
from acknowledged_scorer_status_v2 import AcknowledgedSamplerV2


class Game:
    def __init__(self):
        self.tic = 2
        self.calls = 0

    def get_episode_time(self):
        return self.tic

    def is_episode_finished(self):
        return False

    def advance_action(self, count, update):
        self.calls += 1
        self.tic += 9


class AcknowledgedStatusV2Tests(unittest.TestCase):
    def test_successful_update_is_emitted_before_sample_callback(self):
        events = []
        game = Game()
        def sample(*args, **kwargs):
            self.assertEqual(events[0]["event"], "update_acknowledged")
            return ProgressSample(20, 0, 0, False, False, False)
        sampler = AcknowledgedSamplerV2(sample, "run-v2", events.append, clock_ns=lambda: 10)
        result = sampler(game, None, 5)
        self.assertEqual(game.calls, 1)
        self.assertEqual(events[0]["update_status"], "UPDATE_RETURNED")
        self.assertEqual(events[1]["event"], "sample_result")
        self.assertEqual(events[1]["sample_status"], "AVAILABLE")
        self.assertEqual(result.producer["tic_after"], 11)

    def test_sample_failure_preserves_update_ack_and_producer(self):
        events = []
        game = Game()
        def fail(*args, **kwargs):
            raise ValueError("scorer read failed")
        sampler = AcknowledgedSamplerV2(fail, "run-v2", events.append, clock_ns=lambda: 10)
        with self.assertRaisesRegex(ValueError, "scorer read failed"):
            sampler(game, None, 5)
        self.assertEqual([e["event"] for e in events], ["update_acknowledged", "sample_result"])
        self.assertEqual(events[1]["update_status"], "UPDATE_RETURNED")
        self.assertEqual(events[1]["producer"]["tic_after"], 11)
        self.assertEqual(events[1]["sample_status"], "UNAVAILABLE")
        self.assertEqual(events[1]["error_type"], "ValueError")
        self.assertEqual(game.calls, 1)
        with self.assertRaisesRegex(RuntimeError, "retry refused"):
            sampler(game, None, 5)
        self.assertEqual(game.calls, 1)

    def test_failed_update_never_claims_acknowledgment(self):
        events = []
        game = Game()
        def fail_update(count, update):
            game.calls += 1
            raise OSError("client update failed")
        game.advance_action = fail_update
        sampler = AcknowledgedSamplerV2(lambda *a, **k: self.fail("must not sample"),
                                        "run-v2", events.append, clock_ns=lambda: 10)
        with self.assertRaises(OSError):
            sampler(game, None, 5)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "sample_result")
        self.assertEqual(events[0]["update_status"], "UPDATE_UNAVAILABLE")
        self.assertEqual(events[0]["sample_status"], "NOT_ATTEMPTED")
        self.assertNotIn("producer", events[0])


if __name__ == "__main__":
    unittest.main()
