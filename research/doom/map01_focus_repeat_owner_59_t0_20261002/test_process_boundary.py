"""Process-boundary regression tests for the Issue #59 probe and auditor."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research.doom.map01_focus_repeat_owner_59_t0_20261002.test_audit import valid_raw


ROOT = Path(__file__).resolve().parent
PROBE = ROOT / "probe.py"
AUDIT = ROOT / "audit.py"


class ProcessBoundaryTests(unittest.TestCase):
    def test_preregistration_contains_no_duplicate_json_keys(self):
        def reject_duplicate_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        preregistration = ROOT / "preregistration.json"
        parsed = json.loads(preregistration.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        self.assertEqual(59, parsed["issue"])

    def test_auditor_cli_reads_raw_and_writes_classification_in_separate_process(self):
        raw = valid_raw()
        raw_bytes = (json.dumps(raw, sort_keys=True) + "\n").encode()
        with tempfile.TemporaryDirectory() as temporary:
            raw_path = Path(temporary) / "raw.json"
            report_path = Path(temporary) / "classification.json"
            raw_path.write_bytes(raw_bytes)

            result = subprocess.run(
                [sys.executable, str(AUDIT), "--raw", str(raw_path), "--out", str(report_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(report_path.is_file(), "auditor process must emit its own report")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual("PASS_OWNER_FOCUS_RELEASE_SCOPED", report["status"])
            self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(), hashlib.sha256(raw_path.read_bytes()).hexdigest())

    def test_candidate_does_not_load_or_call_its_raw_auditor(self):
        tree = ast.parse(PROBE.read_text(encoding="utf-8"))
        auditor_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "classify"
        ]
        audit_module_paths = [
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.endswith("audit.py")
        ]
        self.assertEqual([], auditor_calls, "candidate must not classify its own raw output")
        self.assertEqual([], audit_module_paths, "candidate must not dynamically load audit.py")


if __name__ == "__main__":
    unittest.main()
