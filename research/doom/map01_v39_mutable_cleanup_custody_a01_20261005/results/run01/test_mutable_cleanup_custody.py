"""Deterministic synthetic probe for cleanup record mutation after drain."""
import importlib.util
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/doom/map01_v39_mutable_cleanup_custody_a01_20261005/SOURCE"
FIX = SOURCE / "research/doom/map01_v39_cancel_release_fix_a01_20261005"
BRIDGE_TEST = SOURCE / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"


def load():
    spec = importlib.util.spec_from_file_location("custody_base_test", BRIDGE_TEST)
    base = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = base
    spec.loader.exec_module(base)
    harness_module = base.load_v12_test_harness()
    owner = harness_module.load("input_owner_v13_candidate", FIX / "input_owner_v13_candidate.py")
    sys.path.insert(0, str(SOURCE))
    sys.path.insert(0, str(SOURCE / "research/live_control"))
    sys.path.insert(0, str(FIX))
    spec = importlib.util.spec_from_file_location("custody_bridge", FIX / "bridge_v2_candidate.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    harness = harness_module.Harness(owner)
    backend = object.__new__(bridge.Backend)
    backend.owner = harness.owner
    backend.held = {"F8"}
    backend._owner_record_cursor = 0
    backend.events = []
    backend.emit = backend.events.append
    return harness, backend


class MutableCleanupCustody(unittest.TestCase):
    def test_drain_before_owner_final_mutation_leaves_stale_held(self):
        harness, backend = load()
        entered = threading.Event()
        continue_owner = threading.Event()
        record = {"event": "owner_release", "verified": False,
                  "per_key_release_measurements": []}
        def aggregate_reconcile():
            harness.owner.records.append(record)
            entered.set()
            self.assertTrue(continue_owner.wait(2))
            record.update(verified=True, keys_down=[], buttons_down=[], verified_ns=2)
        worker = threading.Thread(target=aggregate_reconcile)
        try:
            worker.start()
            self.assertTrue(entered.wait(1))
            backend._drain_owner_records()
            self.assertEqual(backend._owner_record_cursor, 1)
            continue_owner.set()
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(record["verified"], True)
            # Cursor advancement means the final neutral receipt is never
            # revisited; bridge state remains stale after owner verification.
            self.assertEqual(backend.held, {"F8"})
        finally:
            continue_owner.set()
            worker.join(2)
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
