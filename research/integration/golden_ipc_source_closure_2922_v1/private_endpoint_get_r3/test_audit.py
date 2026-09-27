import copy
import json
import unittest
from pathlib import Path

from audit import audit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RAW = HERE / "raw"
BASE = json.loads((RAW / "session_cli_result.json").read_text())

class ChromiumNavigationAuditTests(unittest.TestCase):
    def test_retained_navigation_passes(self):
        self.assertEqual(audit(BASE, REPO, RAW)["errors"], [])

    def test_rejects_nonprivate_endpoint(self):
        row = copy.deepcopy(BASE); row["session_endpoint_host"] = "example.com"
        self.assertIn("private_loopback", audit(row, REPO, RAW)["errors"])

    def test_rejects_missing_rendered_title(self):
        row = copy.deepcopy(BASE); row["chromium_title_ready_observations"] = 0
        self.assertIn("rendered_page", audit(row, REPO, RAW)["errors"])

    def test_rejects_unverified_release(self):
        row = copy.deepcopy(BASE); row["executor_terminal"]["release"]["verified"] = False
        self.assertIn("release_verified", audit(row, REPO, RAW)["errors"])

    def test_rejects_form_submit_step(self):
        row = copy.deepcopy(BASE); row["form_submit_steps_issued"] = 1
        self.assertIn("no_form_submit", audit(row, REPO, RAW)["errors"])

    def test_rejects_task_output_success(self):
        row = copy.deepcopy(BASE); row["independent_evaluation"]["success"] = True
        self.assertIn("evaluator_no_output", audit(row, REPO, RAW)["errors"])

    def test_rejects_wrong_source_hash(self):
        row = copy.deepcopy(BASE); row["source_sha256"] = dict(row["source_sha256"])
        row["source_sha256"]["research/live_control/session_v4.py"] = "0" * 64
        self.assertIn("source_hash_values", audit(row, REPO, RAW)["errors"])

    def test_rejects_server_post_overclaim(self):
        row = copy.deepcopy(BASE); row["server_POST_count"] = 0
        self.assertIn("server_counter_scope", audit(row, REPO, RAW)["errors"])

if __name__ == "__main__":
    unittest.main()
