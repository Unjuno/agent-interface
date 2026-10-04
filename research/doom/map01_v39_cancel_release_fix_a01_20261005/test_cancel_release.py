import importlib.util
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
FIX_PATH = DOOM / "map01_v39_cancel_release_fix_a01_20261005"
BRIDGE_TEST_PATH = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"
OWNER_V13_PATH = FIX_PATH / "input_owner_v13_candidate.py"
BRIDGE_V2_PATH = FIX_PATH / "bridge_v2_candidate.py"


def load_candidate(config=None):
    spec = importlib.util.spec_from_file_location("bridge_test_for_cancel_fix", BRIDGE_TEST_PATH)
    bridge_test = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_test
    assert spec.loader is not None
    spec.loader.exec_module(bridge_test)
    harness_module = bridge_test.load_v12_test_harness()
    owner_module = harness_module.load("input_owner_v13_candidate", OWNER_V13_PATH)
    sys.path.insert(0, str(FIX_PATH))
    spec = importlib.util.spec_from_file_location("bridge_v2_candidate", BRIDGE_V2_PATH)
    bridge_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_module
    assert spec.loader is not None
    spec.loader.exec_module(bridge_module)
    harness = harness_module.Harness(owner_module, config)
    lease = harness_module.Lease(intent="intent-cancel-fix")
    backend = object.__new__(bridge_module.Backend)
    backend.owner = harness.owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = None
    backend._owner_record_cursor = 0
    backend.events = []
    backend.emit = backend.events.append
    return bridge_test, harness_module, harness, lease, bridge_module, backend


def run_program(bridge_test, backend, lease, program, identifier="cover-cancel-fix", step=4):
    previous = bridge_test.Backend.__bases__[0]
    missing = object()
    prior = previous.__dict__.get("execute", missing)

    def execute(self, _step, _cancel, _identifier, _index):
        return program(self, identifier, step)

    previous.execute = execute
    try:
        return backend.execute({}, lease.cancel, identifier, step)
    finally:
        if prior is missing:
            delattr(previous, "execute")
        else:
            previous.execute = prior


def one_key_cancel(self, _identifier, _step):
    self.raw("F8", True)
    self.lease.cancel.set()


class CancellationReceiptTests(unittest.TestCase):
    def test_cancel_cleanup_emits_up_receipt_joined_to_admission_context(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            down = next(row for row in backend.events if row.get("event") == "input_admission")
            up_rows = [row for row in backend.events
                       if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(up_rows), 1)
            up = up_rows[0]
            self.assertEqual((up.get("id"), up.get("step")), ("cover-cancel-fix", 4))
            self.assertEqual(up["physical_key_measurement"]["actuation_id"],
                             down["physical_key_measurement"]["actuation_id"])
            self.assertEqual(up["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(up["physical_key_measurement"]["identity_status"], "RETIRED")
            self.assertEqual(up["reason"], "cancelled")
        finally:
            harness.close()

    def test_verified_async_cleanup_reconciles_bridge_held_state(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()

    def test_each_cancelled_key_keeps_its_own_admission_context(self):
        bridge_test, hm, harness, lease, _bm, backend = load_candidate()
        hm.owner_module.XK.string_to_keysym = lambda key: {"F8": 8, "F9": 9}[key]
        harness.d.keysym_to_keycode = lambda sym: {8: 74, 9: 75}[sym]

        def two_key_cancel(self, identifier, step):
            self._input_event_context = (identifier, step)
            self.raw("F8", True)
            self._input_event_context = (identifier, step + 1)
            self.raw("F9", True)
            lease.cancel.set()

        try:
            run_program(bridge_test, backend, lease, two_key_cancel, step=10)
            downs = {row["key"]: row for row in backend.events
                     if row.get("event") == "input_admission"}
            ups = {row["key"]: row for row in backend.events
                   if row.get("event") == "input_release_measurement"}
            self.assertEqual(set(ups), {"F8", "F9"})
            self.assertEqual(ups["F8"]["step"], 10)
            self.assertEqual(ups["F9"]["step"], 11)
            for key in ("F8", "F9"):
                self.assertEqual(ups[key]["id"], "cover-cancel-fix")
                self.assertEqual(ups[key]["physical_key_measurement"]["actuation_id"],
                                 downs[key]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()

    def test_ordinary_up_still_emits_one_matching_receipt(self):
        _bt, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            backend._input_event_context = ("ordinary-program", 2)
            backend.raw("F8", True)
            backend._input_event_context = ("ordinary-program", 3)
            backend.raw("F8", False)
            rows = [row for row in backend.events
                    if row.get("event") in {"input_admission", "input_release_measurement"}]
            self.assertEqual([row["event"] for row in rows],
                             ["input_admission", "input_release_measurement"])
            self.assertEqual(rows[0]["physical_key_measurement"]["actuation_id"],
                             rows[1]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(rows[1]["step"], 3)
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()

    def test_unavailable_per_key_samples_never_claim_confirmed_up(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate({"query_fail_on": {4}})
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            ups = [row for row in backend.events
                   if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(ups), 1)
            measurement = ups[0]["physical_key_measurement"]
            self.assertEqual(measurement["classification"], "PHYSICAL_SAMPLE_UNAVAILABLE")
            self.assertIsNone(measurement["adapter_edge"])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
