"""Source-level cleanup contract for the unrun MAP01 v15 successor."""
import unittest

from session_map01_v15 import _GameProxy


class FakeGame:
    def __init__(self, close_error=None):
        self.close_calls = 0
        self.close_error = close_error

    def init(self):
        return "initialized"

    def close(self):
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error
        return "closed"


class GameProxyCleanupTests(unittest.TestCase):
    def test_sample_error_still_closes_inner_game_and_proxy(self):
        sample_error = RuntimeError("final scorer sample failed")
        game = FakeGame()
        proxy = _GameProxy(game, lambda: (_ for _ in ()).throw(sample_error))
        proxy.init()

        with self.assertRaisesRegex(RuntimeError, "final scorer sample failed") as caught:
            proxy.close()

        self.assertIs(caught.exception, sample_error)
        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_sample_error_remains_primary_if_inner_close_also_fails(self):
        sample_error = RuntimeError("final scorer sample failed")
        close_error = OSError("underlying close failed")
        game = FakeGame(close_error)
        proxy = _GameProxy(game, lambda: (_ for _ in ()).throw(sample_error))
        proxy.init()

        with self.assertRaisesRegex(RuntimeError, "final scorer sample failed") as caught:
            proxy.close()

        self.assertIs(caught.exception, sample_error)
        self.assertIs(caught.exception.__cause__, close_error)
        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_inner_close_error_is_propagated_after_state_is_finalized(self):
        close_error = OSError("underlying close failed")
        game = FakeGame(close_error)
        proxy = _GameProxy(game, lambda: None)
        proxy.init()

        with self.assertRaisesRegex(OSError, "underlying close failed"):
            proxy.close()

        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)

    def test_uninitialized_proxy_skips_sample_but_closes_inner(self):
        game = FakeGame()
        samples = []
        proxy = _GameProxy(game, lambda: samples.append("sampled"))

        self.assertEqual(proxy.close(), "closed")
        self.assertEqual(samples, [])
        self.assertEqual(game.close_calls, 1)
        self.assertTrue(proxy.closed)


if __name__ == "__main__":
    unittest.main()
