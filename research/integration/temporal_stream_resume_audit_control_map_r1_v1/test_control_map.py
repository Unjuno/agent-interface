import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_control_map import ORIGINAL_MUTATIONS, row_for_case


class ControlMapTests(unittest.TestCase):
    def test_original_suite_has_ten_distinct_mutations(self):
        self.assertEqual(len(ORIGINAL_MUTATIONS), 10)
        self.assertEqual(len(set(ORIGINAL_MUTATIONS)), 10)
        self.assertIn("control_accept_case48", ORIGINAL_MUTATIONS)

    def test_case_id_48_is_not_assumed_from_row_zero(self):
        batch = {"rows": [
            {"case_id": 45, "parsed": {"candidate": {"parsed": {"status": "OK"}}}},
            {"case_id": 46, "parsed": {"candidate": {"parsed": {"status": "OK"}}}},
            {"case_id": 47, "parsed": {"candidate": {"parsed": {"status": "OK"}}}},
            {"case_id": 48, "parsed": {"mutation": "foreign_epoch", "candidate": {"parsed": {"status": "REFUSE_CHECKPOINT"}}}},
        ]}
        target = row_for_case(batch, 48)
        self.assertEqual(target["parsed"]["mutation"], "foreign_epoch")
        self.assertEqual(target["parsed"]["candidate"]["parsed"]["status"], "REFUSE_CHECKPOINT")

    def test_unique_case_id_lookup_rejects_ambiguous_ids(self):
        with self.assertRaisesRegex(ValueError, "found 2"):
            row_for_case({"rows": [{"case_id": 48}, {"case_id": 48}]}, 48)


if __name__ == "__main__":
    unittest.main()
