import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from coverage_transfer import build_coverage
from frozen_sources import SOURCES
from test_coverage import CALC, DOOM_FEEDBACK, DOOM_OCCUPANCY, DOOM_PHYSICAL


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def frozen_payload():
    sources = {
        name: subprocess.run(["git", "cat-file", "blob", blob], cwd=REPO,
                             check=True, capture_output=True).stdout.decode("utf-8")
        for name, (_, blob) in SOURCES.items()
    }
    return json.dumps({"base_commit": "6968d45197c6a29e717a9281dcd050be1eed90c7", "sources": sources}).encode()


class SeparateAuditTests(unittest.TestCase):
    def run_audit(self, candidate):
        with tempfile.TemporaryDirectory() as directory:
            raw = pathlib.Path(directory) / "candidate.json"
            raw.write_text(json.dumps(candidate), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", "audit.py", "--stdin", str(raw)], cwd=ROOT,
                input=frozen_payload(), check=False, capture_output=True,
            )

    def test_separate_auditor_accepts_candidate_reconstruction(self):
        candidate = build_coverage(DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        completed = self.run_audit(candidate)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["decision"], "PASS")

    def test_separate_auditor_rejects_calc_duration_promotion(self):
        candidate = build_coverage(DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        candidate["domains"]["calc_final_wait"]["held_input_occupancy"]["duration_measured"] = True
        completed = self.run_audit(candidate)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout)["decision"], "FAIL")

    def test_separate_auditor_rejects_state_feedback_as_task_effect(self):
        candidate = build_coverage(DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        candidate["domains"]["doom_v38_v39"]["useful_feedback"]["plan_bound_task_effects"] = 1
        completed = self.run_audit(candidate)
        self.assertEqual(completed.returncode, 1)

    def test_separate_auditor_rejects_v39_gate_promotion(self):
        candidate = build_coverage(DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        candidate["domains"]["doom_v38_v39"]["held_input_occupancy"]["runs"]["v39"]["precision_gate_passed"] = True
        completed = self.run_audit(candidate)
        self.assertEqual(completed.returncode, 1)


if __name__ == "__main__":
    unittest.main()
