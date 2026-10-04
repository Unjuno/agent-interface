import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from acknowledged_scorer_v1 import AcknowledgedSampler
from independent_progress_clock_v2 import ProgressSample, ProgressClock
from map01_scorer_stdio_adapter_v1 import ScorerFileSink
import session_map01_v16 as session


class Game:
    def __init__(self, delta=9, failure=False):
        self.tic = 2
        self.delta = delta
        self.failure = failure
        self.calls = 0
        self.finished = False

    def get_episode_time(self):
        return self.tic

    def is_episode_finished(self):
        return self.finished

    def advance_action(self, count, update):
        assert count == 1 and update is True
        self.calls += 1
        if self.failure:
            raise OSError('update failed')
        self.tic += self.delta


def sample(game, variables, timeout):
    return ProgressSample(100 + game.calls, 0, 0, game.finished, False, False)


class AcknowledgedScorerTests(unittest.TestCase):
    def sampler(self, game=None):
        rows = []
        return AcknowledgedSampler(sample, 'run-a', rows.append, clock_ns=lambda: 10), rows

    def test_multitic_update_reaches_real_sink_with_run_identity(self):
        sampler, rows = self.sampler()
        result = sampler(Game(), None, 10)
        with tempfile.TemporaryDirectory() as directory:
            sink = ScorerFileSink(Path(directory))
            sink.direct(result, lambda: 200)
            payload = sink.samples[0]['payload']
            self.assertEqual(payload['producer']['run_id'], 'run-a')
            self.assertEqual(payload['producer']['tic_after'], 11)
            self.assertEqual(rows[0]['sample'], payload)

    def test_noop_never_returns_a_sample(self):
        sampler, rows = self.sampler()
        with self.assertRaisesRegex(RuntimeError, 'did not advance'):
            sampler(Game(delta=0), None, 10)
        self.assertEqual(rows[0]['status'], 'UPDATE_UNAVAILABLE')
        self.assertIsNone(sampler.last)

    def test_failed_update_is_recorded_without_retry(self):
        sampler, rows = self.sampler()
        game = Game(failure=True)
        with self.assertRaises(OSError):
            sampler(game, None, 10)
        self.assertEqual(game.calls, 1)
        self.assertEqual(rows[0]['error_type'], 'OSError')

    def test_terminal_repeat_carries_ack_without_second_update(self):
        sampler, rows = self.sampler()
        game = Game()
        original = game.advance_action
        def finish(*args):
            original(*args)
            game.finished = True
        game.advance_action = finish
        first = sampler(game, None, 10)
        sampler.sample_fn = lambda *a, **k: ProgressSample(102, 0, 0, True, False, False)
        second = sampler(game, None, 10)
        self.assertEqual(game.calls, 1)
        self.assertEqual(second.producer['update_sequence'], first.producer['update_sequence'])
        self.assertEqual(second.producer['observation_status'], 'TERMINAL_REPEAT_NO_UPDATE')
        clock = ProgressClock()
        clock.ingest(first)
        self.assertEqual(clock.ingest(second), [])

    def test_cross_game_and_cross_thread_are_refused(self):
        sampler, rows = self.sampler()
        sampler(Game(), None, 10)
        with self.assertRaisesRegex(RuntimeError, 'new scorer run'):
            sampler(Game(), None, 10)
        errors = []
        def other_thread():
            try:
                sampler(Game(), None, 10)
            except RuntimeError as error:
                errors.append(str(error))
        worker = threading.Thread(target=other_thread)
        worker.start(); worker.join()
        self.assertEqual(errors, ['scorer update left session main thread'])

    def test_sink_exception_does_not_publish_sample_or_retry(self):
        game = Game()
        attempts = []
        def fail(row):
            attempts.append(row)
            raise OSError('evidence sink failed')
        sampler = AcknowledgedSampler(sample, 'run-a', fail, clock_ns=lambda: 10)
        with self.assertRaises(OSError):
            sampler(game, None, 10)
        self.assertEqual((game.calls, len(attempts)), (1, 1))
        self.assertIsNone(sampler.last)

    def test_session_installs_sampler_and_restores_on_failure(self):
        original = session.previous._coherent_progress_sample
        with tempfile.TemporaryDirectory() as directory:
            def run():
                self.assertIsInstance(session.previous._coherent_progress_sample, AcknowledgedSampler)
                raise OSError('session failure')
            with patch.object(session.previous, '_option', return_value=directory), patch.object(session.previous, 'main', side_effect=run):
                with self.assertRaises(OSError):
                    session.main()
        self.assertIs(session.previous._coherent_progress_sample, original)

    def test_failed_sampler_cannot_update_during_real_proxy_cleanup(self):
        game = Game()
        closed = []
        game.close = lambda: closed.append(True)
        attempts = []
        def fail(row):
            attempts.append(row)
            raise OSError('sink accepted then raised')
        sampler = AcknowledgedSampler(sample, 'run-a', fail, clock_ns=lambda: 10)
        proxy = session.previous._GameProxy(game, lambda: sampler(game, None, 10))
        proxy.initialized = True
        with self.assertRaises(OSError):
            sampler(game, None, 10)
        with self.assertRaises(BaseException):
            proxy.close()
        self.assertEqual((game.calls, len(attempts), closed), (1, 1, [True]))

    def test_update_and_evidence_errors_are_both_retained(self):
        def fail(row):
            raise ValueError('evidence failed')
        sampler = AcknowledgedSampler(sample, 'run-a', fail, clock_ns=lambda: 10)
        with self.assertRaises(BaseException) as caught:
            sampler(Game(failure=True), None, 10)
        self.assertIsInstance(caught.exception, BaseExceptionGroup)
        self.assertEqual([type(e) for e in caught.exception.exceptions], [OSError, ValueError])


if __name__ == '__main__':
    unittest.main()
