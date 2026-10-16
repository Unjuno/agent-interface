import json
import shutil
import tempfile
import unittest
from pathlib import Path

import independent_audit_v2


SOURCE = Path(__file__).resolve().parent


class SavedRunAuditTests(unittest.TestCase):
    def copied_run(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for name in ("FREEZE.json", "RUN.json", "experiment.py", "independent_audit.py", "frozen", "cases"):
            source = SOURCE / name
            target = root / name
            shutil.copytree(source, target) if source.is_dir() else shutil.copy2(source, target)
        return temp, root

    def test_saved_false_pass_is_recomputed_from_sample_history(self):
        temp, root = self.copied_run()
        with temp:
            result = independent_audit_v2.audit(root)
        self.assertEqual("PASS_REPRODUCED_AUDITOR_FALSE_PASS", result["outcome"])
        self.assertEqual("ADMISSION_BRACKETED_PROGRESS", result["baseline_recomputed"])
        self.assertEqual("POST_CANCELLATION_COOCCURRENCE", result["mutated_recomputed"])

    def test_mutated_samples_cannot_be_changed_after_the_saved_audit(self):
        temp, root = self.copied_run()
        with temp:
            raw_path = root / "cases" / "positive_sample_removed" / "raw.json"
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            raw["rows"][1]["samples"][2][1] = 1
            raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = independent_audit_v2.audit(root)
        self.assertEqual("FAIL_AUDIT_V2", result["outcome"])
        self.assertIn("mutated_raw_hash", result["errors"])

    def test_removed_case_row_is_rejected_even_if_run_labels_are_unchanged(self):
        temp, root = self.copied_run()
        with temp:
            raw_path = root / "cases" / "baseline" / "raw.json"
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            raw["rows"].pop()
            raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = independent_audit_v2.audit(root)
        self.assertEqual("FAIL_AUDIT_V2", result["outcome"])
        self.assertTrue(any(error.startswith("audit_input:ValueError:row_set") for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
