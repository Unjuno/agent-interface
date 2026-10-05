"""Construction tests for the new saved-data-only A05 reader."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit_readonly import HERE, inspect_raw, read_json, verify_input_snapshot


class PosthocAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read_json(HERE / "inputs" / "a04-formal" / "RESULT.json")
        cls.freeze = read_json(HERE / "A05_FREEZE.json")

    def test_retained_raw_reconstructs_with_zero_errors(self):
        self.assertEqual(inspect_raw(self.raw), [])

    def test_missing_admission_rejected(self):
        doc = copy.deepcopy(self.raw)
        doc["cases"][0]["events"].pop(0)
        self.assertTrue(inspect_raw(doc))

    def test_aliased_admission_id_rejected(self):
        doc = copy.deepcopy(self.raw)
        events = doc["cases"][0]["events"]
        events[1]["admission_id"] = events[0]["admission_id"]
        self.assertTrue(inspect_raw(doc))

    def test_wrong_release_id_rejected(self):
        doc = copy.deepcopy(self.raw)
        next(row for row in doc["cases"][0]["events"] if row.get("event") == "input_release_transition")["admission_id"] = "wrong"
        self.assertTrue(inspect_raw(doc))

    def test_authority_overclaim_rejected(self):
        doc = copy.deepcopy(self.raw)
        next(row for row in doc["cases"][0]["events"] if row.get("event") == "input_release_transition")["grants_input_authority"] = True
        self.assertTrue(inspect_raw(doc))

    def test_owner_receipt_identity_mismatch_rejected(self):
        doc = copy.deepcopy(self.raw)
        release = next(row for row in doc["cases"][0]["events"] if row.get("event") == "input_release_transition")
        release["owner_keyup_receipt"]["owner_id"] = "different-owner"
        self.assertTrue(inspect_raw(doc))

    def test_float_timestamp_alias_rejected(self):
        doc = copy.deepcopy(self.raw)
        release = next(row for row in doc["cases"][0]["events"] if row.get("event") == "input_release_transition")
        release["owner_keyup_receipt"]["owner_keyup_started_ns"] = float(release["owner_keyup_receipt"]["owner_keyup_started_ns"])
        self.assertTrue(inspect_raw(doc))

    def test_wrong_call_order_rejected(self):
        doc = copy.deepcopy(self.raw)
        doc["cases"][0]["calls"][2:4] = reversed(doc["cases"][0]["calls"][2:4])
        self.assertTrue(inspect_raw(doc))

    def test_non_neutral_fake_keymap_rejected(self):
        doc = copy.deepcopy(self.raw)
        doc["cases"][0]["final_down"] = [38]
        self.assertTrue(inspect_raw(doc))

    def test_tampered_input_is_caught_by_snapshot(self):
        relative = next(iter(self.freeze["inputs_sha256"]))
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copytree(HERE / "inputs", target / "inputs")
            path = target / "inputs" / relative
            path.write_bytes(path.read_bytes() + b"tampered")
            self.assertTrue(verify_input_snapshot(target / "inputs", self.freeze))


if __name__ == "__main__":
    unittest.main()
