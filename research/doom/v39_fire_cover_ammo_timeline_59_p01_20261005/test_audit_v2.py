"""Mutation controls for the versioned saved-result auditor."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[3]
FILES = ("FREEZE.json", "RESULT.json", "audit_v2.py")


class AuditV2MutationTests(unittest.TestCase):
    def run_package(self, mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in FILES:
                shutil.copyfile(PACKAGE / name, target / name)
            result_path = target / "RESULT.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if mutate:
                mutate(result)
                result_path.write_text(json.dumps(result), encoding="utf-8")
            completed = subprocess.run(
                ["python", str(target / "audit_v2.py")], cwd=REPO,
                capture_output=True, text=True, check=True)
            audit = json.loads(completed.stdout)
            return audit

    def assert_mutation_rejected(self, mutate, check):
        audit = self.run_package(mutate)
        self.assertEqual(audit["disposition"], "AUDIT_FAILED")
        self.assertFalse(audit["checks"][check])

    def test_unmodified_result_passes(self):
        audit = self.run_package()
        self.assertEqual(audit["disposition"], "PASS")
        self.assertEqual(audit["passed"], audit["total"])

    def test_disposition_is_reconstructed(self):
        self.assert_mutation_rejected(
            lambda r: r.update(disposition="ZERO_AMMO_EXPOSED"),
            "disposition_matches_raw")

    def test_health_endpoints_are_reconstructed(self):
        self.assert_mutation_rejected(
            lambda r: r["windows"][0].update(health_first_last=[1, 2]),
            "all_window_fields_reconstructed")

    def test_policy_invalidation_is_reconstructed(self):
        self.assert_mutation_rejected(
            lambda r: r["windows"][2].update(policy_invalidation_signal=None),
            "all_window_fields_reconstructed")

    def test_wait_duration_is_reconstructed(self):
        self.assert_mutation_rejected(
            lambda r: r["windows"][0].update(model_wait_ms=-1),
            "all_window_fields_reconstructed")

    def test_cover_actions_are_reconstructed(self):
        self.assert_mutation_rejected(
            lambda r: r["windows"][0].update(cover_actions=["strafe_left"]),
            "all_window_fields_reconstructed")


if __name__ == "__main__":
    unittest.main()
