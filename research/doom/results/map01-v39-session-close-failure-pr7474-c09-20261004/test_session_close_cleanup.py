"""Regression for MAP01 v15 final-scorer failure cleanup."""
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


DOOM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DOOM))

# The proxy itself has no game dependency. Stub only the two module-level
# imports so this test exercises the exact session wrapper without ViZDoom.
for name, attrs in {
    "map01_scorer_stdio_adapter_v1": {
        "MainThreadScorerStdin": type("Poller", (), {}),
        "ScorerFileSink": type("Sink", (), {}),
    },
    "independent_progress_clock_v2": {
        "ProgressSample": type("ProgressSample", (), {}),
    },
}.items():
    module = types.ModuleType(name)
    for attr, value in attrs.items():
        setattr(module, attr, value)
    sys.modules[name] = module

source_override = os.environ.get("SESSION_MAP01_V15_SOURCE")
if source_override:
    spec = importlib.util.spec_from_file_location(
        "session_map01_v15_under_test", source_override
    )
    candidate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = candidate
    spec.loader.exec_module(candidate)
else:
    import session_map01_v15 as candidate


class FakeGame:
    def __init__(self, close_error=None):
        self.close_calls = 0
        self.close_error = close_error

    def init(self):
        return True

    def close(self):
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error
        return "game-closed"


class FinalScorerFailureCleanupTests(unittest.TestCase):
    def test_final_sample_failure_still_closes_game_and_marks_proxy_closed(self):
        sample_error = RuntimeError("final scorer sample failed")
        game = FakeGame()
        proxy = candidate._GameProxy(game, lambda: (_ for _ in ()).throw(sample_error))
        proxy.init()

        with self.assertRaises(RuntimeError) as caught:
            proxy.close()

        self.assertIs(caught.exception, sample_error)
        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_sample_and_game_close_failures_are_both_preserved(self):
        sample_error = RuntimeError("final scorer sample failed")
        close_error = OSError("game close failed")
        game = FakeGame(close_error)
        proxy = candidate._GameProxy(game, lambda: (_ for _ in ()).throw(sample_error))
        proxy.init()

        with self.assertRaises(RuntimeError) as caught:
            proxy.close()

        self.assertIs(caught.exception, sample_error)
        self.assertIs(caught.exception.__cause__, close_error)
        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)


if __name__ == "__main__":
    unittest.main()
