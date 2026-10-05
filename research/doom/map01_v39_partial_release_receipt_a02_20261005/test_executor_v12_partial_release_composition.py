"""ExecutorV12 expiry composition for a two-key cleanup exception schedule."""
import importlib.util
import os
import json
import sys
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "research" / "doom" / "map01_v39_cancel_release_fix_a01_20261005"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "frozen_live_control"))
os.environ.setdefault("V13_OWNER_CANDIDATE_PATH", str(HERE / "input_owner_v13_candidate.py"))

import executor_v12
from lease import Expired

test_spec = importlib.util.spec_from_file_location(
    "cancel_release_for_executor_composition", FIX / "test_cancel_release.py")
candidate_tests = importlib.util.module_from_spec(test_spec)
assert test_spec.loader is not None
test_spec.loader.exec_module(candidate_tests)


class ExecutorV12PartialReleaseCompositionTests(unittest.TestCase):
    def test_expiry_partial_up_is_published_before_verified_terminal_recovery(self):
        bridge_test, _hm, harness, _lease, _bridge, backend = candidate_tests.load_candidate()
        owner_module = sys.modules["input_owner_v13_candidate"]
        owner_module.XK.string_to_keysym = lambda key: {"F8": 8, "F9": 9, "b": 10}[key]
        harness.d.keysym_to_keycode = lambda sym: {8: 74, 9: 75, 10: 76}[sym]

        prior_lease_type = executor_v12.Lease

        class ObservedLease(prior_lease_type):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.expected_focus = 42
                self.intent_token = "intent-v12-partial-release-a01"

        executor_v12.Lease = ObservedLease
        parent = bridge_test.Backend.__bases__[0]
        missing = object()
        prior_execute = parent.__dict__.get("execute", missing)
        prior_release = parent.__dict__.get("release_all", missing)
        real_fake_input = owner_module.xtest.fake_input
        key_release_calls = []
        events = []
        terminal_seen = threading.Event()

        def fail_once_on_second_key_release(display, event_type, code=None, **kwargs):
            if event_type == owner_module.X.KeyRelease:
                key_release_calls.append(code)
                if len(key_release_calls) == 2:
                    raise RuntimeError("injected second key release")
            return real_fake_input(display, event_type, code, **kwargs)

        def emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_seen.set()

        def hold_until_owner_expiry(self, _step, _cancel, _identifier, _index):
            self._input_event_context = ("v12-partial-expiry", 4)
            self.raw("F8", True)
            self._input_event_context = ("v12-partial-expiry", 5)
            self.raw("F9", True)
            deadline = time.monotonic() + 1.5
            while time.monotonic() < deadline:
                if any(row.get("event") == "owner_release"
                       and row.get("release_error_type") == "RuntimeError"
                       for row in harness.owner.records):
                    raise Expired()
                time.sleep(0.001)
            raise AssertionError("owner expiry did not retain its partial cleanup record")

        def retry_remaining_release(self):
            try:
                record = self.owner.call("release", self.lease)
                self._drain_owner_records()
                state = self.owner.call("input_state", self.lease)
                verified = (record.get("verified") is True
                            and state.get("owned_keycodes") == []
                            and state.get("owned_buttons") == [])
                return {"verified": verified}
            finally:
                self._drain_owner_records()

        parent.execute = hold_until_owner_expiry
        parent.release_all = retry_remaining_release
        owner_module.xtest.fake_input = fail_once_on_second_key_release
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = executor_v12.Executor(backend, emit)
        try:
            deadline = time.perf_counter_ns() + 70_000_000
            executor.submit("v12-partial-expiry-a01", [{"op": "hold"}], 1, deadline)
            self.assertTrue(terminal_seen.wait(2.0), repr(events))

            partial = [row for row in harness.owner.records
                       if row.get("event") == "owner_release"
                       and row.get("release_error_type") == "RuntimeError"]
            self.assertEqual(len(partial), 1)
            self.assertEqual([row["key"] for row in partial[0]["per_key_release_measurements"]],
                             ["F8"])
            self.assertFalse(partial[0]["verified"])

            ups = [row for row in events if row.get("event") == "input_release_measurement"]
            self.assertEqual([(row.get("key"), row.get("step")) for row in ups],
                             [("F8", 4), ("F9", 5)])
            self.assertEqual([row["physical_key_measurement"]["classification"] for row in ups],
                             ["CONFIRMED_PHYSICAL_UP", "CONFIRMED_PHYSICAL_UP"])
            terminals = [row for row in events if row.get("event") == "terminal"]
            self.assertEqual(len(terminals), 1)
            self.assertEqual(terminals[0]["status"], "expired")
            self.assertTrue(terminals[0]["release"]["verified"])
            names = [row.get("event") for row in events]
            self.assertEqual(key_release_calls, [74, 75, 75])
            release_positions = [i for i, name in enumerate(names)
                                 if name == "input_release_measurement"]
            self.assertEqual(len(release_positions), 2)
            self.assertLess(release_positions[-1], names.index("terminal"))
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())

            injections_before = len(harness.d.injections)
            backend._input_event_context = ("after-owner-fault", 1)
            with self.assertRaisesRegex(RuntimeError, "input owner failed closed"):
                backend.raw("b", True)
            self.assertEqual(len(harness.d.injections), injections_before)
            self.assertNotIn(76, harness.d.physical)
            raw_path = Path(os.environ.get(
                "EXECUTOR_V12_RAW_OUTPUT", HERE / "executor-v12-partial-release-raw.json"))
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(
                json.dumps({
                    "key_release_attempts": key_release_calls,
                    "partial_owner_release": partial[0],
                    "release_measurements": ups,
                    "event_order": names,
                    "terminal": terminals[0],
                    "fake_physical_after_terminal": sorted(harness.d.physical),
                    "bridge_held_after_terminal": sorted(backend.held),
                    "later_down_rejected": True,
                    "injections_before_rejected_down": injections_before,
                    "injections_after_rejected_down": len(harness.d.injections),
                }, indent=2, sort_keys=True) + "\n")
        finally:
            executor.close()
            owner_module.xtest.fake_input = real_fake_input
            harness.close()
            if prior_execute is missing:
                delattr(parent, "execute")
            else:
                parent.execute = prior_execute
            if prior_release is missing:
                delattr(parent, "release_all")
            else:
                parent.release_all = prior_release
            executor_v12.Lease = prior_lease_type


if __name__ == "__main__":
    unittest.main(verbosity=2)
