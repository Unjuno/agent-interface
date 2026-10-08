import copy
import json
import unittest
from pathlib import Path

from audit import audit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RAW = HERE / "raw"
BASE = json.loads((RAW / "session_cli_result.json").read_text())

class SessionCliAuditTests(unittest.TestCase):
    def test_raw_allocation_passes(self):
        self.assertEqual(audit(BASE, REPO, RAW)["errors"], [])

    def test_rejects_missing_ready(self):
        row = copy.deepcopy(BASE); row["ready_event"] = False
        self.assertIn("ready", audit(row, REPO, RAW)["errors"])

    def test_rejects_http_failure(self):
        row = copy.deepcopy(BASE); row["http_status"] = 500
        self.assertIn("HTTP_200", audit(row, REPO, RAW)["errors"])

    def test_rejects_task_submit(self):
        row = copy.deepcopy(BASE); row["submit_commands"] = 1
        self.assertIn("no_submit", audit(row, REPO, RAW)["errors"])

    def test_rejects_input_admission(self):
        row = copy.deepcopy(BASE); row["input_admission_events"] = 1
        self.assertIn("no_input", audit(row, REPO, RAW)["errors"])

    def test_rejects_wrong_source_closure(self):
        row = copy.deepcopy(BASE); row["source_sha256"] = dict(row["source_sha256"])
        row["source_sha256"]["research/live_control/session_v4.py"] = "0" * 64
        self.assertIn("source_sha256_values", audit(row, REPO, RAW)["errors"])

    def test_rejects_wrong_image(self):
        row = copy.deepcopy(BASE); row["runtime_image"] = "sha256:" + "0" * 64
        self.assertIn("image", audit(row, REPO, RAW)["errors"])

    def test_rejects_uninstrumented_server_claim(self):
        row = copy.deepcopy(BASE); row["server_POST_count"] = 0
        self.assertIn("server_POST_honest", audit(row, REPO, RAW)["errors"])

if __name__ == "__main__":
    unittest.main()
