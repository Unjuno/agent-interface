import json
import unittest
from pathlib import Path

import audit_raw


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "preflight-01" / "data.json"


class IndependentDataAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text(encoding="utf-8"))

    def test_raw_hash_matches_frozen_digest(self):
        self.assertEqual(audit_raw.sha(RAW), audit_raw.EXPECTED_INPUT)

    def test_all_three_seeds_and_984_rows_reconcile(self):
        self.assertEqual(audit_raw.validate(self.raw), [])
        self.assertEqual(sum(len(v) for s in self.raw["seeds"] for v in s["splits"].values()), 984)

    def test_seven_independent_mutations_are_rejected(self):
        mutations = audit_raw.controls(self.raw)
        self.assertEqual(len(mutations), 7)
        self.assertTrue(all(x["rejected"] for x in mutations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
