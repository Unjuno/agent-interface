import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RetainedResultTests(unittest.TestCase):
    def test_formal_invocations_and_exits(self):
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        self.assertEqual(record["candidate_invocations"], 1)
        self.assertEqual(record["auditor_invocations"], 1)
        self.assertEqual(record["retries"], 0)
        self.assertEqual(record["candidate_exit"], 0)
        self.assertEqual(record["auditor_exit"], 0)

    def test_audited_nonincremental_result(self):
        candidate = json.loads((ROOT / "results/candidate-out/candidate.json").read_text())
        audit = json.loads((ROOT / "results/audit-out/audit.json").read_text())
        self.assertEqual(len(candidate["rows"]), 36)
        self.assertEqual(audit["case_count"], 36)
        self.assertEqual(audit["raw_reconstruction"], "PASS")
        self.assertEqual(audit["method_disposition"], "NO_INCREMENTAL_VALUE")
        self.assertTrue(audit["mutation_controls"]["timestamp_substitution_rejected"])
        self.assertTrue(audit["mutation_controls"]["track_substitution_rejected"])
        comparisons = audit["matched_budget_comparison"]
        self.assertEqual([x["false_yield_budget"] for x in comparisons], list(range(7)))
        self.assertTrue(all(x["ttc_best_tp"] == 24 for x in comparisons))
        self.assertTrue(all(x["simple_best_tp"] == [24, 24] for x in comparisons))
        self.assertFalse(any(x["strictly_better_than_both"] for x in comparisons))

    def test_frozen_source_frame_and_output_hashes(self):
        frozen = json.loads((ROOT / "FROZEN.json").read_text())
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        for name, digest in frozen["source_sha256"].items():
            self.assertEqual(sha(ROOT / name), digest, name)
        self.assertEqual(len(frozen["frame_sha256"]), 180)
        for name, digest in frozen["frame_sha256"].items():
            self.assertEqual(sha(ROOT / name), digest, name)
        self.assertEqual(sha(ROOT / "results/candidate-out/candidate.json"), record["candidate_sha256"])
        self.assertEqual(sha(ROOT / "results/audit-out/audit.json"), record["audit_sha256"])

    def test_retained_package_checksum_manifest(self):
        entries = (ROOT / "SHA256SUMS.txt").read_text().splitlines()
        self.assertGreater(len(entries), 180)
        for entry in entries:
            digest, relative = entry.split("  ", 1)
            self.assertEqual(sha(ROOT / relative.removeprefix("./")), digest, relative)


if __name__ == "__main__":
    unittest.main()
