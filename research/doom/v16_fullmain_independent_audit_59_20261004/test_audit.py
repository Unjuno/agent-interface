import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit import SOURCE, audit


REPO = Path(__file__).resolve().parents[3]


class V16FullmainAuditTests(unittest.TestCase):
    def test_retained_record_passes_scoped_audit(self):
        result = audit(REPO)
        self.assertEqual(result["audit"], "PASS_SCOPED_V16_FULLMAIN_NO_ACTION")
        self.assertEqual(result["construction02"]["scorer_samples"], 2)
        self.assertEqual(result["construction02"]["positive_useful_events"], 0)
        self.assertTrue(result["construction02"]["post_score_precedes_close_release"])

    def test_nonempty_close_release_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(REPO / SOURCE, copy / SOURCE)
            path = copy / SOURCE / "construction02/out/session/owner-events.json"
            owner = json.loads(path.read_text(encoding="utf-8"))
            owner[0]["keys_down"] = ["left"]
            path.write_text(json.dumps(owner), encoding="utf-8")
            result = audit(copy)
        self.assertIn("construction02_owner_release_not_verified_empty", result["errors"])

    def test_positive_event_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(REPO / SOURCE, copy / SOURCE)
            path = copy / SOURCE / "construction02/out/session/scorer-summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            summary["event_count"] = 1
            path.write_text(json.dumps(summary), encoding="utf-8")
            result = audit(copy)
        self.assertIn("construction02_useful_event_summary_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
