import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "research" / "doom" / "map01_v39_cancel_release_fix_a01_20261005"
HERE = Path(__file__).resolve().parent
os.environ.setdefault("V13_OWNER_CANDIDATE_PATH",
                      str(HERE / "input_owner_v13_candidate.py"))

spec = importlib.util.spec_from_file_location(
    "cancel_release_candidate_tests", FIX / "test_cancel_release.py")
candidate_tests = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate_tests)


class PartialReleaseReceiptTests(unittest.TestCase):
    def test_confirmed_first_key_up_survives_second_key_release_exception(self):
        bridge_test, owner_harness, harness, lease, _bridge_module, backend = (
            candidate_tests.load_candidate())
        owner_module = sys.modules["input_owner_v13_candidate"]
        owner_module.XK.string_to_keysym = lambda key: {"F8": 8, "F9": 9, "b": 10}[key]
        harness.d.keysym_to_keycode = lambda sym: {8: 74, 9: 75, 10: 76}[sym]
        backend._input_event_context = ("partial-release", 10)
        backend.raw("F8", True)
        backend._input_event_context = ("partial-release", 11)
        backend.raw("F9", True)
        self.assertEqual(backend.held, {"F8", "F9"})
        self.assertEqual(harness.d.physical, {74, 75})

        real_fake_input = owner_module.xtest.fake_input
        seen_key_releases = []

        def fail_second_key_release(display, event_type, code=None, **kwargs):
            if event_type == owner_module.X.KeyRelease:
                seen_key_releases.append(code)
                if len(seen_key_releases) == 2:
                    raise RuntimeError("injected second key release")
            return real_fake_input(display, event_type, code, **kwargs)

        owner_module.xtest.fake_input = fail_second_key_release
        try:
            try:
                harness.owner.call("release", lease)
            except RuntimeError as exc:
                release_exception = str(exc)
            else:
                self.fail("second-key release exception did not propagate")
            backend._drain_owner_records()

            records = [row for row in harness.owner.records
                       if row.get("event") == "owner_release"]
            self.assertEqual(len(records), 1)
            partial = records[0]
            self.assertFalse(partial["verified"])
            self.assertNotIn("keys_down", partial)
            receipts = partial["per_key_release_measurements"]
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["key"], "F8")
            self.assertEqual(receipts[0]["step"], 10)
            self.assertEqual(receipts[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")

            emitted = [row for row in backend.events
                       if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0]["key"], "F8")
            self.assertEqual(emitted[0]["id"], "partial-release")
            self.assertEqual(emitted[0]["step"], 10)
            self.assertEqual(backend.held, {"F9"})
            self.assertEqual(harness.d.physical, {75})

            injections_before = len(harness.d.injections)
            try:
                harness.owner.call("down", lease, "b")
            except RuntimeError as exc:
                subsequent_down_error = str(exc)
            else:
                self.fail("faulted owner admitted a later down")
            self.assertEqual(len(harness.d.injections), injections_before)
            (HERE / "raw.json").write_text(json.dumps({
                "release_exception": release_exception,
                "owner_release_records": records,
                "emitted_release_rows": emitted,
                "backend_held_after_failure": sorted(backend.held),
                "fake_physical_after_failure": sorted(harness.d.physical),
                "subsequent_down_error": subsequent_down_error,
                "injection_count_after_cleanup_failure": injections_before,
                "injection_count_after_rejected_down": len(harness.d.injections),
            }, indent=2, sort_keys=True) + "\n")
        finally:
            owner_module.xtest.fake_input = real_fake_input
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
