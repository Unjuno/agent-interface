import copy
import json
from pathlib import Path
import unittest

from audit import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((Path(__file__).parent / "baseline.json").read_text(encoding="utf-8"))

    def test_retained_baseline_reconstructs_its_gaps(self):
        result = audit(self.raw)
        self.assertEqual((result["rows"], result["prestart_representation_gaps"], result["prestart_terminal_gaps"]), (210, 40, 20))

    def test_incomplete_and_duplicate_coverage_are_rejected(self):
        for rows in (self.raw["rows"][:-1], self.raw["rows"] + [self.raw["rows"][0]]):
            with self.subTest(count=len(rows)):
                bad = copy.deepcopy(self.raw)
                bad["rows"] = rows
                with self.assertRaises(ValueError):
                    audit(bad)

    def test_decision_and_type_corruptions_are_rejected(self):
        corruptions = (("terminal_accepted", True), ("representation_accepted", False),
                       ("started_ns", False), ("verified", 0), ("observed_ns", "0"))
        for field, value in corruptions:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.raw)
                bad["rows"][0][field] = value
                with self.assertRaises(ValueError):
                    audit(bad)

    def test_missing_extra_and_nonobject_rows_are_rejected(self):
        for operation in ("missing", "extra", "null"):
            with self.subTest(operation=operation):
                bad = copy.deepcopy(self.raw)
                if operation == "missing":
                    del bad["rows"][0]["observed_ns"]
                elif operation == "extra":
                    bad["rows"][0]["extra"] = 0
                else:
                    bad["rows"][0] = None
                with self.assertRaises(ValueError):
                    audit(bad)

    def test_wrong_revision_and_source_identity_are_rejected(self):
        for field, value in (("revision", "fixed"), ("source_sha256", "not-a-sha")):
            with self.subTest(field=field):
                bad = copy.deepcopy(self.raw)
                bad[field] = value
                with self.assertRaises(ValueError):
                    audit(bad)


if __name__ == "__main__":
    unittest.main()
