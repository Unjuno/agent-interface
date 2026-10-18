import json
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
INPUTS = PACKAGE / "inputs"


class SourceAttributionTests(unittest.TestCase):
    def load_api(self):
        for module in ("candidate", "audit"):
            self.assertTrue((PACKAGE / f"{module}.py").is_file(), f"{module}.py must exist")
        sys.path.insert(0, str(PACKAGE))
        try:
            return importlib.import_module("candidate"), importlib.import_module("audit")
        finally:
            sys.path.pop(0)

    def test_candidate_classifies_the_retained_run_as_v12_base_without_v15_overlay(self):
        candidate, _ = self.load_api()
        result = candidate.build_result(INPUTS)
        self.assertEqual(result["schema"], "v39-release-source-attribution-v1")
        self.assertEqual(result["observed_source_count"], 20)
        self.assertEqual(result["frozen_tree_hash_matches"], 17)
        self.assertEqual(result["historical_tree_hash_matches"], 3)
        self.assertEqual(result["v15_measurement_sources_present"], [])
        self.assertEqual(result["v12_backend_owner_chain"], [
            "doom/session_map01_v12.py",
            "doom/doom_typed_release_backend_v1.py",
            "live_control/input_owner_v10.py",
        ])
        self.assertEqual(result["owner_release_rows"], 13)
        self.assertEqual(result["owner_release_rows_with_per_key_timing"], 0)
        self.assertFalse(result["owner_v10_contains_per_key_timing_fields"])
        self.assertFalse(result["launch_selection_proven"])

    def test_independent_audit_reconstructs_result_from_frozen_inputs(self):
        candidate, auditor = self.load_api()
        result = candidate.build_result(INPUTS)
        audit = auditor.audit_result(INPUTS, result)
        self.assertEqual(audit["status"], "PASS_SOURCE_ATTRIBUTION")
        self.assertEqual(audit["checks_passed"], audit["checks_total"])

    def test_independent_audit_rejects_changed_classification(self):
        candidate, auditor = self.load_api()
        result = candidate.build_result(INPUTS)
        result["v15_measurement_sources_present"] = ["doom/session_map01_v15.py"]
        audit = auditor.audit_result(INPUTS, result)
        self.assertEqual(audit["status"], "FAIL_SOURCE_ATTRIBUTION")
        self.assertIn("result_matches_independent_reconstruction", audit["failed_checks"])

    def test_independent_audit_rejects_unlisted_result_fields(self):
        candidate, auditor = self.load_api()
        result = candidate.build_result(INPUTS)
        result["unsupported_claim"] = True
        audit = auditor.audit_result(INPUTS, result)
        self.assertEqual(audit["status"], "FAIL_SOURCE_ATTRIBUTION")
        self.assertIn("result_matches_independent_reconstruction", audit["failed_checks"])

    def test_independent_audit_rejects_mutated_source_snapshot(self):
        candidate, auditor = self.load_api()
        result = candidate.build_result(INPUTS)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            copied_package = tmp_path / "package"
            shutil.copytree(PACKAGE / "inputs", copied_package / "inputs")
            shutil.copy2(PACKAGE / "FREEZE.json", copied_package / "FREEZE.json")
            source = copied_package / "inputs/executed_sources/live_control/input_owner_v10.py"
            source.write_bytes(source.read_bytes() + b"\n# mutation\n")
            audit = auditor.audit_result(copied_package / "inputs", result)
        self.assertEqual(audit["status"], "FAIL_SOURCE_ATTRIBUTION")
        self.assertIn("frozen_inputs_reconstruct", audit["failed_checks"])

    def test_candidate_refuses_to_overwrite_an_existing_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "RESULT.json"
            output.write_text("preserve-me\n", encoding="utf-8")
            completed = subprocess.run(
                [os.environ.get("PYTHON", "python"), "-B", str(PACKAGE / "candidate.py"),
                 "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve-me\n")


if __name__ == "__main__":
    unittest.main()
