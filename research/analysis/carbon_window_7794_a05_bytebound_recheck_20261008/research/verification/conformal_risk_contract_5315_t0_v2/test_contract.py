import json
import unittest
from pathlib import Path

from candidate import check_certificate, crc_upper


class SuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).parent
        cls.cal = json.loads((cls.root / "calibration.json").read_text())
        cls.raw = (cls.root / "calibration_records.json").read_bytes()
        cls.records = json.loads(cls.raw)
        cls.arm = json.loads((cls.root / "scenarios.json").read_text())["arms"][0]

    def test_exact_retained_bytes_are_bound(self):
        self.assertEqual(check_certificate(self.cal, self.arm, self.raw, self.records), "ALLOW_MARGINAL_CLAIM_ONLY")
        bad = dict(self.cal, calibration_digest="sha256:tampered-nonempty")
        self.assertEqual(check_certificate(bad, self.arm, self.raw, self.records), "REJECT_CALIBRATION_DIGEST_MISMATCH")

    def test_rows_and_summary_must_agree(self):
        bad = dict(self.cal, errors=7)
        self.assertEqual(check_certificate(bad, self.arm, self.raw, self.records), "REJECT_CALIBRATION_STATS_MISMATCH")

    def test_conditional_scope_is_not_inferred_from_marginal_crc(self):
        bad = dict(self.cal, claim_scope="CONDITIONAL_SELECTED_RISK")
        self.assertEqual(check_certificate(bad, self.arm, self.raw, self.records), "REJECT_UNSUPPORTED_SCOPE")

    def test_crc_boundary(self):
        self.assertAlmostEqual(crc_upper(199, 8, 1), 0.045)


if __name__ == "__main__":
    unittest.main()
