import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("executor_v13.py")

# The tested method is loaded from the exact PR blob. These stubs only satisfy
# imports and class inheritance; the harness does not invoke parent behavior.
def install_stub(name, **members):
    module = types.ModuleType(name)
    for key, value in members.items():
        setattr(module, key, value)
    sys.modules[name] = module

install_stub("executor_v3", Cancelled=type("Cancelled", (Exception,), {}),
             DecisionRequired=type("DecisionRequired", (Exception,), {}))
install_stub("executor_v12", Executor=type("Previous", (), {}))
install_stub("lease", Expired=type("Expired", (Exception,), {}))
spec = importlib.util.spec_from_file_location("executor_v13_exact_head", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Executor = module.Executor

class Lease:
    def __init__(self):
        self.cancel = threading.Event()
    def interruption_snapshot(self):
        return None
    def is_set(self):
        return False

class Backend:
    def release_all(self):
        error = KeyboardInterrupt("cleanup sink interrupt")
        error.release_batch_publication = {
            "status": "delivery_unknown", "position": 0,
        }
        raise error

class CleanupBaseExceptionTests(unittest.TestCase):
    def test_cleanup_interrupt_escapes_before_terminal_without_custody(self):
        events = []
        lease = Lease()
        executor = Executor.__new__(Executor)
        executor.backend = Backend()
        executor.emit = events.append
        executor.lock = threading.RLock()
        executor.active = ("audit", lease)
        executor.release_watch_stops = {}

        with self.assertRaisesRegex(KeyboardInterrupt, "cleanup sink interrupt") as caught:
            executor._run_with_watcher_cleanup("audit", [], lease)

        self.assertEqual(caught.exception.release_batch_publication, {
            "status": "delivery_unknown", "position": 0,
        })
        self.assertFalse(any(row.get("event") == "terminal" for row in events), events)

if __name__ == "__main__":
    unittest.main(verbosity=2)
