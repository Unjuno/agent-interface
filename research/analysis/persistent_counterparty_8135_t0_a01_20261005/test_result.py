import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RetainedResultTests(unittest.TestCase):
    def test_one_candidate_one_audit_no_retry(self):
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        self.assertEqual((record["candidate_invocations"], record["auditor_invocations"], record["retries"]), (1, 1, 0))
        self.assertEqual((record["candidate_exit"], record["auditor_exit"]), (0, 0))

    def test_method_audit_and_mutations(self):
        audit = json.loads((ROOT / "results/audit-out/audit.json").read_text())
        self.assertEqual((audit["block_count"], audit["case_count"]), (40, 80))
        self.assertEqual(audit["method_disposition"], "METHOD_PASS_SCOPED")
        self.assertEqual(audit["mutation_rejections"], 5)
        self.assertTrue(all(x == "REJECTED" for x in audit["mutation_controls"].values()))
        self.assertEqual(audit["effect_audit"]["unauthorized_effect"], 0)
        self.assertEqual(audit["persistent_later_profile_by_previous_public_event"]["H_FAST"]["addon"], 4)
        self.assertEqual(audit["frequency_sham_later_profile_by_previous_public_event"]["H_FAST"], {"positive": 2, "addon": 2})

    def test_frozen_hashes_and_checksum_manifest(self):
        frozen = json.loads((ROOT / "FROZEN.json").read_text())
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        for name, digest in frozen["source_sha256"].items():
            self.assertEqual(sha(ROOT / name), digest, name)
        self.assertEqual(sha(ROOT / "bundle/manifest.json"), frozen["manifest_sha256"])
        self.assertEqual(sha(ROOT / "bundle/sealed_truth.json"), frozen["truth_sha256"])
        self.assertEqual(sha(ROOT / "results/candidate-out/candidate.json"), record["candidate_sha256"])
        self.assertEqual(sha(ROOT / "results/audit-out/audit.json"), record["audit_sha256"])
        for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines():
            digest, rel = line.split("  ", 1)
            self.assertEqual(sha(ROOT / rel.removeprefix("./")), digest, rel)


if __name__ == "__main__":
    unittest.main()
