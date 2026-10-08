import copy
import json
import unittest
from pathlib import Path

from audit import audit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASE = json.loads((HERE / "RESULT.json").read_text())

class AuditTests(unittest.TestCase):
    def test_retained_result_passes(self):
        self.assertEqual(audit(BASE, REPO)["errors"], [])

    def test_rejects_wrong_status(self):
        item = copy.deepcopy(BASE); item["http_status"] = 503
        self.assertIn("HTTP_200", audit(item, REPO)["errors"])

    def test_rejects_output_mutation(self):
        item = copy.deepcopy(BASE); item["output_exists_after"] = True
        self.assertIn("no_output_after", audit(item, REPO)["errors"])

    def test_rejects_wrong_seed(self):
        item = copy.deepcopy(BASE); item["seed"] = 992924
        self.assertIn("seed", audit(item, REPO)["errors"])

    def test_rejects_probe_hash_mismatch(self):
        item = copy.deepcopy(BASE); item["probe_source_sha256"] = "0" * 64
        self.assertIn("probe_source_hash", audit(item, REPO)["errors"])

    def test_rejects_probe_post_claim_mismatch(self):
        item = copy.deepcopy(BASE); item["probe_POST_calls_issued"] = 1
        self.assertIn("no_probe_POST", audit(item, REPO)["errors"])

    def test_rejects_uninstrumented_server_claim(self):
        item = copy.deepcopy(BASE); item["server_POST_count"] = 0
        self.assertIn("honest_POST_scope", audit(item, REPO)["errors"])

if __name__ == "__main__":
    unittest.main()
