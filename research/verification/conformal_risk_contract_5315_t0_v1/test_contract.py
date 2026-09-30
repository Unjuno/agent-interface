import json
import unittest
from pathlib import Path

from candidate import check_certificate, crc_upper


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((Path(__file__).parent / "scenarios.json").read_text())

    def test_finite_sample_expression(self):
        self.assertAlmostEqual(crc_upper(199, 8, 1), 0.045)

    def test_only_marginal_crc_scope_is_supported(self):
        cal = dict(self.fixture["calibration"])
        arm = dict(self.fixture["arms"][0])
        self.assertEqual(check_certificate(cal, arm), "ALLOW_MARGINAL_CLAIM_ONLY")
        cal["claim_scope"] = "CONDITIONAL_SELECTED_RISK"
        self.assertEqual(check_certificate(cal, arm), "REJECT_UNSUPPORTED_SCOPE")

    def test_population_version_freshness_and_assumption_binding(self):
        cal = dict(self.fixture["calibration"])
        for key, value, expected in (
            ("population_id", "other", "REJECT_POPULATION_MISMATCH"),
            ("version", "other", "REJECT_VERSION_MISMATCH"),
            ("age_hours", 25, "REJECT_STALE"),
            ("exchangeable", False, "REJECT_ASSUMPTION_INVALID"),
        ):
            arm = dict(self.fixture["arms"][0])
            if key in ("population_id", "version", "age_hours"):
                arm[key] = value
            else:
                cal[key] = value
            self.assertEqual(check_certificate(cal, arm), expected)
            cal = dict(self.fixture["calibration"])


if __name__ == "__main__":
    unittest.main()
