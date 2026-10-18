import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class ProvenanceCorrectionTests(unittest.TestCase):
    def test_branch_label_mismatch_is_explicit_and_base_is_exact(self):
        frozen = json.loads((ROOT / "FROZEN.json").read_text())
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        correction = (ROOT / "PROVENANCE_CORRECTION.md").read_text()
        self.assertEqual(frozen["branch"], "research/8135-persistent-counterparty-t0-a02-20261005")
        self.assertIn("research/8135-persistent-counterparty-t0-a01-20261005", correction)
        self.assertEqual(frozen["base_commit"], "b6907899f11b036f2af572e8d4794ebb4b7e5c83")
        self.assertEqual(record["candidate_invocations"], 1)
        self.assertEqual(record["auditor_invocations"], 1)


if __name__ == "__main__":
    unittest.main()
