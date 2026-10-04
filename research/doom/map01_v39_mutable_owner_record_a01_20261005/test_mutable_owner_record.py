import importlib.util
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
PACKAGE = DOOM / "map01_v39_mutable_owner_record_a01_20261005"
BRIDGE_TEST = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"


def load_candidate():
    spec = importlib.util.spec_from_file_location("mutable_owner_bridge_test", BRIDGE_TEST)
    bridge_test = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_test
    spec.loader.exec_module(bridge_test)
    hm = bridge_test.load_v12_test_harness()
    owner = hm.load("input_owner_v13_mutable_successor",
                    PACKAGE / "input_owner_v13_candidate.py")
    sys.path.insert(0, str(PACKAGE))
    spec = importlib.util.spec_from_file_location(
        "bridge_v2_mutable_successor", PACKAGE / "bridge_v2_candidate.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    harness = hm.Harness(owner)
    lease = hm.Lease(intent="intent-mutable-owner-record")
    backend = object.__new__(bridge.Backend)
    backend.owner = harness.owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = ("mutable-owner-record", 12)
    backend._owner_record_cursor = 0
    backend._pending_owner_record_indices = set()
    backend._emitted_owner_release_rows = set()
    backend.events = []
    backend.emit = backend.events.append
    return hm, harness, lease, backend


class MutableOwnerRecordTests(unittest.TestCase):
    def test_same_partial_record_is_revisited_after_verified_empty_update(self):
        hm, harness, lease, backend = load_candidate()
        real_query_pointer = hm.Root.__dict__["query_pointer"]
        aggregate_blocked = threading.Event()
        allow_aggregate = threading.Event()

        def block_aggregate_query(root):
            aggregate_blocked.set()
            if not allow_aggregate.wait(1.0):
                raise RuntimeError("test aggregate-query barrier timed out")
            return real_query_pointer(root)

        hm.Root.query_pointer = block_aggregate_query
        release_errors = []
        try:
            backend.raw("F8", True)
            harness.d.query_fail_on.add(harness.d.query_i + 2)

            def release_owner():
                try:
                    harness.owner.call("release", lease)
                except Exception as exc:
                    release_errors.append(exc)

            worker = threading.Thread(target=release_owner, daemon=True)
            worker.start()
            if not aggregate_blocked.wait(1.0):
                self.fail(f"owner missed aggregate barrier: {release_errors!r}")
            self.assertEqual(len(harness.owner.records), 1)
            record = harness.owner.records[0]
            self.assertIs(record["verified"], False)
            self.assertNotIn("keys_down", record)
            backend._drain_owner_records()
            self.assertEqual(backend._owner_record_cursor, 1)
            self.assertEqual(backend.held, {"F8"})

            allow_aggregate.set()
            worker.join(1.0)
            self.assertFalse(worker.is_alive())
            self.assertEqual(release_errors, [])
            self.assertIs(record["verified"], True)
            self.assertEqual(record["keys_down"], [])
            backend._drain_owner_records()
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
            rows = [row for row in backend.events
                    if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["physical_key_measurement"]["classification"],
                             "PHYSICAL_SAMPLE_UNAVAILABLE")
        finally:
            allow_aggregate.set()
            hm.Root.query_pointer = real_query_pointer
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
