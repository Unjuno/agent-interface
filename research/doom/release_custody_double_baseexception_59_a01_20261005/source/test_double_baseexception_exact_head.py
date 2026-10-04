import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("executor_v13.py")
def install_stub(name, **members):
    module = types.ModuleType(name)
    for key, value in members.items(): setattr(module, key, value)
    sys.modules[name] = module
install_stub("executor_v3", Cancelled=type("Cancelled", (Exception,), {}),
             DecisionRequired=type("DecisionRequired", (Exception,), {}))
install_stub("executor_v12", Executor=type("Previous", (), {}))
install_stub("lease", Expired=type("Expired", (Exception,), {}))
spec = importlib.util.spec_from_file_location("executor_v13_exact_head", SOURCE)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
Executor = module.Executor

STEP_LEDGER = {"source": "step", "ledger": "A"}
CLEANUP_LEDGER = {"source": "cleanup", "ledger": "B"}
class Lease:
    cancel = threading.Event()
    def interruption_snapshot(self): return None
    def is_set(self): return False
class Backend:
    def execute(self, step, lease, identifier, index):
        error = KeyboardInterrupt("worker interruption")
        error.release_batch_publication = STEP_LEDGER
        raise error
    def release_all(self):
        error = KeyboardInterrupt("cleanup interruption")
        error.release_batch_publication = CLEANUP_LEDGER
        raise error
class DoubleBaseExceptionTests(unittest.TestCase):
    def test_cleanup_ledger_replaces_step_ledger_in_terminal(self):
        events=[]; lease=Lease(); executor=Executor.__new__(Executor)
        executor.backend=Backend(); executor.emit=events.append
        executor.lock=threading.RLock(); executor.active=("double",lease)
        executor.release_watch_stops={}
        with self.assertRaisesRegex(KeyboardInterrupt, "worker interruption") as caught:
            executor._run_with_watcher_cleanup("double", [{"op":"noop"}], lease)
        self.assertIs(caught.exception.release_batch_publication, STEP_LEDGER)
        terminal=next(row for row in events if row.get("event")=="terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["error"], "KeyboardInterrupt('cleanup interruption')")
        self.assertEqual(terminal["release"]["release_batch_delivery"], CLEANUP_LEDGER)
        self.assertNotEqual(terminal["release"].get("release_batch_delivery"), STEP_LEDGER)
if __name__ == "__main__": unittest.main(verbosity=2)
