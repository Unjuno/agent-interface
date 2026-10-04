"""Regression for cancellation after the cause sample and before fake KeyRelease."""
import threading
import time
import unittest
import sys
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))
import test_executor_owner_cancel_cause_v1 as fixture


class PostSampleVisibility:
    """Make a separate cancellation setter visible only after one false sample."""

    def __init__(self, owner_thread, release_dequeued):
        self.owner_thread = owner_thread
        self.release_dequeued = release_dequeued
        self.pending = threading.Event()
        self.visible = threading.Event()
        self.sampled = threading.Event()
        self.sample_false_ns = None
        self.cancel_visible_ns = None
        self.keyup_ns = None

    def set(self):
        self.pending.set()

    def is_set(self):
        if threading.get_ident() != self.owner_thread:
            return self.pending.is_set()
        if not self.release_dequeued.is_set() or not self.pending.is_set():
            return False
        if not self.sampled.is_set():
            self.sample_false_ns = time.perf_counter_ns()
            self.sampled.set()
            return False
        return self.visible.is_set()

    def wait(self, timeout=None):
        return self.pending.wait(timeout)


class PostSamplePublicationTests(unittest.TestCase):
    def test_post_sample_cancel_release_is_published_before_cancel_terminal(self):
        owner, displays, constants, dequeued, lease_slot, owner_thread, saved = (
            fixture.make_owner())
        events = []
        backend = fixture.Backend(owner, lease_slot)
        executor = fixture.executor_v12.Executor(backend, events.append)
        setter = None
        xtest = sys.modules["Xlib.ext.xtest"]
        original_fake_input = xtest.fake_input
        try:
            executor.submit("post-sample", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 5_000_000_000)
            self.assertTrue(backend.started.wait(1))
            deadline = time.monotonic() + 1
            while not displays and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertTrue(displays)

            lease = executor.active[1]
            worker = executor.active[2]
            cancel = PostSampleVisibility(owner_thread, dequeued)
            lease.cancel = cancel

            def fake_input_before_keyup(connection, event, code):
                if event == constants.KeyRelease:
                    self.assertTrue(cancel.visible.wait(1))
                    cancel.keyup_ns = time.perf_counter_ns()
                return original_fake_input(connection, event, code)

            xtest.fake_input = fake_input_before_keyup

            def expose_cancel_after_sample():
                self.assertTrue(cancel.sampled.wait(1))
                cancel.cancel_visible_ns = time.perf_counter_ns()
                cancel.visible.set()

            setter = threading.Thread(target=expose_cancel_after_sample,
                                      name="post-sample-cancel-setter")
            setter.start()
            self.assertTrue(executor.cancel("post-sample"))
            backend.continue_step.set()
            self.assertTrue(dequeued.wait(1))
            worker.join(1)
            setter.join(1)
            self.assertFalse(worker.is_alive())
            self.assertFalse(setter.is_alive())

            print("POST_SAMPLE_RAW_EVENTS", repr(events))
            released = next(row for row in events if row["event"] == "input_released")
            terminal = next(row for row in events if row["event"] == "terminal")
            self.assertLess(cancel.sample_false_ns, cancel.cancel_visible_ns)
            self.assertLess(cancel.cancel_visible_ns, cancel.keyup_ns)
            self.assertEqual(released["owner_release"]["reason"], "cancelled")
            self.assertTrue(released["owner_release"]["verified"])
            self.assertEqual(released["owner_release"]["keys_down"], [])
            self.assertEqual(released["owner_release"]["buttons_down"], [])
            self.assertLess(released["published_ns"], terminal["terminal_ns"])
            self.assertEqual(terminal["status"], "cancelled")
            self.assertEqual(displays[0].events,
                             [(constants.KeyPress, 38), (constants.KeyRelease, 38)])
            print("POST_SAMPLE_PUBLICATION_ORDER",
                  f"sample_false_ns={cancel.sample_false_ns}",
                  f"cancel_visible_ns={cancel.cancel_visible_ns}",
                  f"fake_keyup_ns={cancel.keyup_ns}",
                  f"owner_reason={released['owner_release']['reason']}",
                  f"release_published_ns={released['published_ns']}",
                  f"terminal={terminal['status']}",
                  f"terminal_ns={terminal['terminal_ns']}")
        finally:
            xtest.fake_input = original_fake_input
            backend.continue_step.set()
            if setter is not None:
                setter.join(1)
            executor.close()
            owner.close()
            sys.modules.pop("owner_under_test", None)
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
