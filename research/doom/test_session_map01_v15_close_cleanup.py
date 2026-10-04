import sys, types, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
for name in ("map01_scorer_stdio_adapter_v1", "independent_progress_clock_v2"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["map01_scorer_stdio_adapter_v1"].MainThreadScorerStdin = type("Polling", (), {})
sys.modules["map01_scorer_stdio_adapter_v1"].ScorerFileSink = type("Sink", (), {})
sys.modules["independent_progress_clock_v2"].ProgressSample = type("ProgressSample", (), {})
import session_map01_v15 as candidate

class FakeGame:
    def __init__(self, error=None): self.error, self.close_calls = error, 0
    def close(self):
        self.close_calls += 1
        if self.error: raise self.error
        return "closed"

class ProxyCloseTests(unittest.TestCase):
    def test_final_sample_failure_still_closes_game_and_marks_proxy_closed(self):
        sample_error = RuntimeError("final scorer sample failed")
        inner = FakeGame()
        proxy = candidate._GameProxy(inner, lambda: (_ for _ in ()).throw(sample_error))
        proxy.initialized = True
        with self.assertRaisesRegex(RuntimeError, "final scorer sample failed") as raised:
            proxy.close()
        self.assertIs(raised.exception, sample_error)
        self.assertEqual(inner.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_close_failure_is_preserved_when_final_sample_also_fails(self):
        sample_error = RuntimeError("final scorer sample failed")
        close_error = OSError("game close failed")
        inner = FakeGame(close_error)
        proxy = candidate._GameProxy(inner, lambda: (_ for _ in ()).throw(sample_error))
        proxy.initialized = True
        with self.assertRaisesRegex(RuntimeError, "final scorer sample failed") as raised:
            proxy.close()
        self.assertIs(raised.exception.__cause__, close_error)
        self.assertEqual(inner.close_calls, 1)
        self.assertTrue(proxy.closed)

if __name__ == "__main__": unittest.main(verbosity=2)

