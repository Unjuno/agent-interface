import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).parent


class CandidateContractTests(unittest.TestCase):
    def test_candidate_emits_exact_read_only_modes_and_retains_release_obligation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate.json"
            run = subprocess.run(
                [sys.executable, str(HERE / "candidate.py"), "--spec", str(HERE / "spec.json"), "--output", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            cases = {row["case_id"]: row for row in result["cases"]}
            self.assertEqual(len(cases), 9)
            self.assertEqual(cases["independent_telemetry_loss"]["binary"], [])
            self.assertEqual(
                [row["operation"] for row in cases["independent_telemetry_loss"]["contract"]],
                ["inspect_raw", "present_semantics", "preview_plan", "show_effect_receipt"],
            )
            self.assertEqual(
                [row["operation"] for row in cases["common_semantic_scheduler_stall"]["contract"]],
                ["inspect_raw"],
            )
            self.assertEqual(cases["release_channel_loss"]["release_obligation"], "MANDATORY_RELEASE")
            self.assertTrue(all(row["operation"] != "dispatch_action" for case in cases.values() for row in case["contract"]))


if __name__ == "__main__":
    unittest.main()
