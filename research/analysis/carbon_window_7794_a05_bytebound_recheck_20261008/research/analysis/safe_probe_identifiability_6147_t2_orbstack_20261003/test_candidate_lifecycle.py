import unittest

from lifecycle import close_display


class ClosedDisplay:
    def close(self):
        raise ConnectionClosedError("Xvfb closed after final reset")


class OpenDisplay:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class ConnectionClosedError(Exception):
    pass


class CandidateLifecycleTests(unittest.TestCase):
    def test_close_tolerates_only_x_server_disconnect(self):
        close_display(ClosedDisplay(), ConnectionClosedError)

    def test_close_still_closes_live_display(self):
        display = OpenDisplay()
        close_display(display, ConnectionClosedError)
        self.assertTrue(display.closed)

    def test_unrelated_close_errors_propagate(self):
        class BrokenDisplay:
            def close(self):
                raise RuntimeError("unexpected close failure")

        with self.assertRaisesRegex(RuntimeError, "unexpected close failure"):
            close_display(BrokenDisplay(), ConnectionClosedError)


if __name__ == "__main__":
    unittest.main()
