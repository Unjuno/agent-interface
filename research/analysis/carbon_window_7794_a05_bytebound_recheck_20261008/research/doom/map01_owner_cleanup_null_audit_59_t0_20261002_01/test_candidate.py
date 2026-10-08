import copy
import json
from pathlib import Path
import unittest

from candidate import classify

RAW = json.loads((Path(__file__).parent / "predecessor_raw.json").read_text(encoding="utf-8"))


class CleanupNullAuditTests(unittest.TestCase):
    def test_accepts_null_key_only_for_owner_cleanup_row(self):
        result = classify(copy.deepcopy(RAW))
        self.assertEqual("PASS_OWNER_OCCURRENCE_BOUNDARY_SCOPED", result["status"])
        self.assertTrue(result["checks"]["cleanup_null_key_bound_to_keycode_owner_intent"])

    def test_rejects_null_key_on_explicit_up(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[0]["key"] = None
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])

    def test_rejects_cleanup_keycode_mismatch(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[1]["keycode"] = 26
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])

    def test_rejects_cross_owner_cleanup(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[1]["owner_id"] = "different-owner"
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])

    def test_rejects_wrong_cleanup_reason(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[1]["reason"] = "explicit_up"
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])

    def test_rejects_missing_terminal_empty_keymap(self):
        raw = copy.deepcopy(RAW)
        raw["fake_server_keymap_snapshots"] = []
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])

    def test_rejects_inverted_release_bracket(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[1]["request_returned_ns"] = rows[1]["request_started_ns"] - 1
        self.assertEqual("FAIL_OWNER_BOUNDARY", classify(raw)["status"])


if __name__ == "__main__":
    unittest.main()

