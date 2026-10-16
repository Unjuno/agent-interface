"""The retained-source projection must keep release, observation and task effect distinct."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
CANDIDATE = PACKAGE / "candidate.py"


class CandidateTransferTests(unittest.TestCase):
    def test_two_domains_keep_visual_change_separate_from_exact_task_effect(self):
        with tempfile.TemporaryDirectory(prefix="handback-transfer-") as temp:
            output = Path(temp) / "candidate.json"
            run = subprocess.run(
                [sys.executable, str(CANDIDATE), "--repo-root", str(REPO),
                 "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "PASS_RETAINED_SOURCE_TRANSFER_CANDIDATE")
        by_id = {row["case_id"]: row for row in result["records"]}
        doom = by_id["doom-v39-first-plan-frames"]
        self.assertEqual(doom["evidence_type"], "OBSERVED_CHANGE")
        self.assertEqual(doom["task_effect"], "UNRESOLVED")
        self.assertEqual(doom["semantic_task_feedback"], "unverified")
        self.assertFalse(doom["map_exit"])
        self.assertEqual(doom["frame_count"], 3)

        release = by_id["doom-v39-typed-revocation-release"]
        self.assertEqual(release["evidence_type"], "PHYSICAL_RELEASE")
        self.assertEqual(release["typed_emit_to_release_ms"], 26.090)
        self.assertEqual(release["task_effect"], "UNRESOLVED")

        desktop = by_id["browser-direct-task6-save"]
        self.assertEqual(desktop["evidence_type"], "TASK_EFFECT")
        self.assertEqual(desktop["task_effect"], "EXACT_ONCE_SUBMISSION")
        self.assertTrue(desktop["visual_acknowledgement"] == "UNKNOWN_NOT_OBSERVED")
        self.assertTrue(desktop["physical_release_verified"])
        self.assertTrue(all(not row["input_authority"]
                            and not row["semantic_authority"]
                            for row in result["records"]))


if __name__ == "__main__":
    unittest.main()
