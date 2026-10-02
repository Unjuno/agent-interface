from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"


class FreezeIntegrityTests(unittest.TestCase):
    def test_freeze_blobs_match_the_recorded_sha256_sidecar(self):
        freeze = FIXTURES / "allocation-02-FREEZE.json"
        expected = (FIXTURES / "allocation-02-FREEZE.sha256").read_text(encoding="ascii").split()[0]
        self.assertEqual(hashlib.sha256(freeze.read_bytes()).hexdigest(), expected)

    def test_formal_workflow_hash_is_reconstructible_from_sparse_checkout_fixture(self):
        expected_workflow = "b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2"
        freezes = (
            FIXTURES / "allocation-01-FREEZE.json",
            FIXTURES / "allocation-02-FREEZE.json",
        )
        for path in freezes:
            with self.subTest(freeze=path.name):
                freeze = json.loads(path.read_text(encoding="utf-8"))
                matches = [value for name, value in freeze["source_sha256"].items()
                           if name.endswith(".github/workflows/analysis-index.yml")]
                self.assertEqual(matches, [expected_workflow])

        # The hash is asserted as a literal because Actions checks out only
        # research/analysis; the workflow blob is outside that sparse tree.

    def test_run_record_hashes_match_retained_result_fixtures(self):
        record = json.loads((FIXTURES / "RUN_RECORD.json").read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "REPLICATION_PASS_WITH_GEOMETRY_HOLD")
        self.assertEqual(record["candidate_invocations"], 1)
        self.assertEqual(record["auditor_invocations"], 1)
        self.assertEqual(record["retries"], 0)
        self.assertEqual(record["artifact_sha256"]["candidate/raw.json"],
                         "4092bc96be090a5a441abac0adc07db44a5855247e06c68785caedf57bf2e38f")
        self.assertEqual(record["artifact_sha256"]["audit/AUDIT.json"],
                         "43680c27ff963be62f4b29900c987ba3e6266d9adb1a06a8d375826bcad79d5d")


if __name__ == "__main__":
    unittest.main()
