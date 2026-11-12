import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
PACKAGE = Path(__file__).resolve().parent
OWNER_PATH = PACKAGE / "input_owner_v13_candidate.py"
BRIDGE_PATH = PACKAGE / "bridge_v2_candidate.py"
BRIDGE_TEST_PATH = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"


def load_candidate(config=None):
    spec = importlib.util.spec_from_file_location("bridge_test_for_durable_release", BRIDGE_TEST_PATH)
    bridge_test = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_test
    assert spec.loader is not None
    spec.loader.exec_module(bridge_test)
    harness_module = bridge_test.load_v12_test_harness()
    owner_module = harness_module.load("input_owner_v13_candidate", OWNER_PATH)
    sys.path.insert(0, str(PACKAGE))
    spec = importlib.util.spec_from_file_location("bridge_v2_candidate", BRIDGE_PATH)
    bridge_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_module
    assert spec.loader is not None
    spec.loader.exec_module(bridge_module)
    harness = harness_module.Harness(owner_module, config)
    lease = harness_module.Lease(intent="intent-release-durability")
    backend = object.__new__(bridge_module.Backend)
    backend.owner = harness.owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = None
    backend._owner_record_cursor = 0
    backend.events = []
    backend.emit = backend.events.append
    return bridge_test, harness, lease, bridge_module, backend


def run_program(bridge_test, backend, lease, program):
    previous = bridge_test.Backend.__bases__[0]
    missing = object()
    prior = previous.__dict__.get("execute", missing)

    def execute(self, _step, _cancel, identifier, index):
        return program(self, identifier, index)

    previous.execute = execute
    try:
        return backend.execute({}, lease.cancel, "release-query-failure", 3)
    finally:
        if prior is missing:
            delattr(previous, "execute")
        else:
            previous.execute = prior


class ReleaseRecordDurabilityTests(unittest.TestCase):
    def test_aggregate_keymap_failure_preserves_confirmed_per_key_up_without_neutral_claim(self):
        bridge_test, harness, lease, _bridge_module, backend = load_candidate({"query_fail_on": {5}})
        release_errors = []

        def release_after_admission(self, identifier, step):
            self._input_event_context = (identifier, step)
            self.raw("F8", True)
            try:
                self.owner.call("release", self.lease)
            except RuntimeError as exc:
                release_errors.append(str(exc))

        try:
            run_program(bridge_test, backend, lease, release_after_admission)
            rows = [row for row in backend.events if row.get("event") == "input_release_measurement"]
            owner_releases = [row for row in harness.owner.records if row.get("event") == "owner_release"]
            record = owner_releases[0] if owner_releases else None
            print("RAW_RESULT " + json.dumps({
                "aggregate_query_number": harness.d.query_i,
                "release_errors": release_errors,
                "release_rows": [{"key": row.get("key"), "id": row.get("id"),
                                  "step": row.get("step"),
                                  "actuation_id": row.get("physical_key_measurement", {}).get("actuation_id"),
                                  "classification": row.get("physical_key_measurement", {}).get("classification")}
                                 for row in rows],
                "owner_release": None if record is None else {
                    "verified": record.get("verified"),
                    "verification_status": record.get("verification_status"),
                    "keys_down": record.get("keys_down"),
                    "buttons_down": record.get("buttons_down"),
                    "verification_error": record.get("verification_error")},
                "bridge_held": sorted(backend.held),
                "fake_physical": sorted(harness.d.physical)}, sort_keys=True))

            self.assertEqual(release_errors, ["sample failure"])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(rows[0]["key"], "F8")
            admission = next(row for row in backend.events if row.get("event") == "input_admission")
            self.assertEqual((rows[0]["id"], rows[0]["step"]), ("release-query-failure", 3))
            self.assertEqual(rows[0]["physical_key_measurement"]["actuation_id"],
                             admission["physical_key_measurement"]["actuation_id"])
            self.assertEqual(len(owner_releases), 1)
            self.assertFalse(owner_releases[0]["verified"])
            self.assertEqual(owner_releases[0]["verification_status"], "UNAVAILABLE")
            self.assertIsNone(owner_releases[0]["keys_down"])
            self.assertIsNone(owner_releases[0]["buttons_down"])
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
