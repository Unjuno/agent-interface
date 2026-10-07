"""Force the release publisher to lag the worker's terminal boundary."""
import threading
import time
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import executor_v12
import test_executor_owner_cancel_cause_v1 as fixture


class GatedPublisherExecutor(executor_v12.Executor):
    def __init__(self, backend, emit):
        super().__init__(backend, emit)
        self.publisher_started = threading.Event()
        self.allow_publisher = threading.Event()

    def _publish_release(self, identifier, lease):
        self.publisher_started.set()
        if not self.allow_publisher.wait(2):
            return
        return super()._publish_release(identifier, lease)


class ReleaseReturnBackend(fixture.Backend):
    def __init__(self, owner, lease_slot):
        super().__init__(owner, lease_slot)
        self.release_returned = threading.Event()

    def release_all(self):
        result = super().release_all()
        self.release_returned.set()
        return result


class ReleasePublicationOrderTests(unittest.TestCase):
    def test_release_publication_finishes_before_terminal(self):
        owner, displays, constants, dequeued, lease_slot, owner_thread, saved = fixture.make_owner()
        events = []
        terminal_seen = threading.Event()

        def emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_seen.set()

        backend = ReleaseReturnBackend(owner, lease_slot)
        executor = GatedPublisherExecutor(backend, emit)
        try:
            executor.submit("ordered", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 5_000_000_000)
            self.assertTrue(backend.started.wait(1))
            lease = executor.active[1]
            worker = executor.active[2]
            lease.cancel = fixture.DeferredOwnerVisibility(owner_thread)
            self.assertTrue(executor.cancel("ordered"))
            self.assertTrue(executor.publisher_started.wait(1))
            backend.continue_step.set()
            self.assertTrue(dequeued.wait(1))
            self.assertTrue(backend.release_returned.wait(1))

            # The publisher is deliberately held after the owner's verified
            # interruption exists. A correct executor must not terminalize yet.
            terminal_while_publisher_blocked = terminal_seen.wait(.1)
            executor.allow_publisher.set()
            worker.join(1)
            self.assertFalse(worker.is_alive())
            for watcher in executor.release_watchers:
                watcher.join(1)
                self.assertFalse(watcher.is_alive())

            self.assertFalse(
                terminal_while_publisher_blocked,
                "terminal was emitted while the cancel-release publisher was gated",
            )
            released = next(row for row in events if row["event"] == "input_released")
            terminal = next(row for row in events if row["event"] == "terminal")
            self.assertEqual(released["owner_release"]["reason"], "cancelled")
            self.assertTrue(released["owner_release"]["verified"])
            self.assertLess(released["published_ns"], terminal["terminal_ns"])
            self.assertEqual(terminal["status"], "cancelled")
            self.assertEqual(displays[0].events,
                             [(constants.KeyPress, 38), (constants.KeyRelease, 38)])
        finally:
            backend.continue_step.set()
            executor.allow_publisher.set()
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
