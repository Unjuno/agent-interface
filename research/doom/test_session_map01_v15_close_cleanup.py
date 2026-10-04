import sys, types, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
for name in ("map01_scorer_stdio_adapter_v1", "independent_progress_clock_v2"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["map01_scorer_stdio_adapter_v1"].MainThreadScorerStdin = type("Polling", (), {})
sys.modules["map01_scorer_stdio_adapter_v1"].ScorerFileSink = type("Sink", (), {})
sys.modules["independent_progress_clock_v2"].ProgressSample = type("ProgressSample", (), {})
import session_map01_v15 as candidate


class FakeGame:
    def __init__(self, error=None):
        self.error = error
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        if self.error:
            raise self.error
        return "closed"


class ProxyCloseTests(unittest.TestCase):
    def make_proxy(self, inner=None, sample_error=None):
        inner = inner or FakeGame()
        samples = []

        def sample():
            samples.append(True)
            if sample_error:
                raise sample_error

        proxy = candidate._GameProxy(inner, sample)
        proxy.initialized = True
        return proxy, inner, samples

    def test_repeated_close_samples_and_closes_once(self):
        proxy, inner, samples = self.make_proxy()
        self.assertEqual(proxy.close(), "closed")
        self.assertIsNone(proxy.close())
        self.assertEqual(samples, [True])
        self.assertEqual(inner.close_calls, 1)

    def test_sample_failure_still_closes_game(self):
        sample_error = RuntimeError("final scorer sample failed")
        proxy, inner, _ = self.make_proxy(sample_error=sample_error)
        with self.assertRaises(RuntimeError) as raised:
            proxy.close()
        self.assertIs(raised.exception, sample_error)
        self.assertEqual(inner.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_sample_and_close_failures_are_both_retained(self):
        sample_error = RuntimeError("final scorer sample failed")
        close_error = OSError("game close failed")
        proxy, inner, _ = self.make_proxy(FakeGame(close_error), sample_error)
        with self.assertRaises(BaseExceptionGroup) as raised:
            proxy.close()
        self.assertEqual(raised.exception.exceptions, (sample_error, close_error))
        self.assertEqual(inner.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_unwinding_controller_and_both_cleanup_failures_are_retained(self):
        controller_error = ValueError("controller failed")
        sample_error = RuntimeError("final scorer sample failed")
        close_error = OSError("game close failed")
        proxy, inner, _ = self.make_proxy(FakeGame(close_error), sample_error)
        try:
            raise controller_error
        except ValueError:
            with self.assertRaises(BaseExceptionGroup) as raised:
                proxy.close()
        self.assertEqual(
            raised.exception.exceptions,
            (controller_error, sample_error, close_error),
        )
        self.assertEqual(inner.close_calls, 1)
        self.assertTrue(proxy.closed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
