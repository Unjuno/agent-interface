"""Tests for the raw-only auditor's independent completion oracle."""

import importlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CASE_IDS = ["control", "bool_false", "float_zero", "null", "string_zero",
            "missing_code", "duplicate_success", "success_plus_failure"]
EXITS = [0, 0, 0, 1, 1, 1, 1, 0]
EXPECTED_COMPLETIONS = [
    [{"event": "runner_complete", "exit_code": 0}],
    [{"event": "runner_complete", "exit_code": False}],
    [{"event": "runner_complete", "exit_code": 0.0}],
    [{"event": "runner_complete", "exit_code": None}],
    [{"event": "runner_complete", "exit_code": "0"}],
    [{"event": "runner_complete"}],
    [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 0}],
    [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 1}],
]


class IndependentOracleTests(unittest.TestCase):
    def load(self):
        try:
            return importlib.import_module("independent_audit")
        except ModuleNotFoundError:
            return None

    def test_literal_expected_completion_cases_and_oracle(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 raw-only auditor must exist")
        for case_id, exit_code, expected in zip(CASE_IDS, EXITS, EXPECTED_COMPLETIONS):
            actual = module.expected_completion_rows(case_id)
            self.assertEqual(actual, expected)
            self.assertEqual(module.completion_exit(actual), exit_code)

    def test_oracle_preserves_typed_zero_equality_witnesses(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 raw-only auditor must exist")
        self.assertEqual(module.completion_exit([{"event": "runner_complete", "exit_code": False}]), 0)
        self.assertEqual(module.completion_exit([{"event": "runner_complete", "exit_code": 0.0}]), 0)
        self.assertEqual(module.completion_exit([
            {"event": "runner_complete", "exit_code": 0},
            {"event": "runner_complete", "exit_code": 1},
        ]), 0)
        self.assertEqual(module.completion_exit([
            {"event": "runner_complete", "exit_code": 0},
            {"event": "runner_complete", "exit_code": 0},
        ]), 1)

    def test_case_validator_rejects_unregistered_mutation(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 raw-only auditor must exist")
        self.assertTrue(module.completion_rows_match("bool_false", EXPECTED_COMPLETIONS[1]))
        self.assertFalse(module.completion_rows_match("bool_false", EXPECTED_COMPLETIONS[0]))

    def test_bundle_audit_accepts_hand_built_complete_bundle_and_detects_raw_mutation(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 raw-only auditor must exist")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            result = root / "result"
            target.mkdir()
            result.mkdir()
            expected = {"allocation": "MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01",
                        "frozen_main": "7c44e41934a62b6f90227b0dc74231cf897ab898", "cases": {}}
            target_files = {
                "audit_formal_x11.py": b"frozen target cli\n",
                "EXPECTED.json": (json.dumps(expected, sort_keys=True) + "\n").encode(),
                "test_audit_formal_x11.py": (
                    "def fixture_rows():\n"
                    f"    return [{{'event':'fixture','allocation':'{expected['allocation']}',"
                    f"'frozen_main':'{expected['frozen_main']}','synthetic_only':True,"
                    "'evidence_mode':'synthetic-cli'}, {'event':'runner_start','sequence':1}, "
                    "{'event':'runner_complete','exit_code':0}]\n").encode(),
            }
            frozen = {}
            for name, data in target_files.items():
                (target / name).write_bytes(data)
                frozen[name] = (hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                                hashlib.sha256(data).hexdigest())
            baseline = [{"event": "fixture", "allocation": expected["allocation"],
                         "frozen_main": expected["frozen_main"], "synthetic_only": True,
                         "evidence_mode": "synthetic-cli"}, {"event": "runner_start", "sequence": 1}]
            manifest = {"allocation": module.ALLOCATION, "disposition": "CANDIDATE_EXPECTED",
                        "target_git_blob": frozen["audit_formal_x11.py"][0],
                        "target_sha256": frozen["audit_formal_x11.py"][1],
                        "expected_git_blob": frozen["EXPECTED.json"][0],
                        "expected_sha256": frozen["EXPECTED.json"][1],
                        "fixture_git_blob": frozen["test_audit_formal_x11.py"][0],
                        "fixture_sha256": frozen["test_audit_formal_x11.py"][1],
                        "runner_sha256": module.RUNNER_SHA256,
                        "matrix_sha256": module.MATRIX_SHA256, "cases": []}
            with patch.dict(module.FROZEN, frozen):
                for case_id, exit_code, completion in zip(CASE_IDS, EXITS, EXPECTED_COMPLETIONS):
                    folder = result / case_id
                    folder.mkdir()
                    raw = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                                   for row in baseline + completion)
                    (folder / "raw.jsonl").write_bytes(raw)
                    audit = {"status": "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if exit_code == 0 else "FAIL_AUDIT",
                             "errors": [] if exit_code == 0 else ["expected target rejection"],
                             "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_rows": len(baseline + completion),
                             "expected_sha256": manifest["expected_sha256"], "allocation": expected["allocation"],
                             "host_launch_receipt_sha256": None, "host_launch_receipt_authenticated": False,
                             "host_launch_receipt_bindings_valid": False,
                             "scope": "synthetic JSONL only; no X server or physical input evidence"}
                    audit_bytes = (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode()
                    stdout_bytes = (json.dumps(audit, sort_keys=True) + "\n").encode()
                    (folder / "audit.json").write_bytes(audit_bytes)
                    (folder / "stdout.txt").write_bytes(stdout_bytes)
                    (folder / "stderr.txt").write_bytes(b"")
                    entry = {"case_id": case_id, "expected_exit": exit_code, "actual_exit": exit_code}
                    for key, rel, data in (("raw", f"{case_id}/raw.jsonl", raw),
                                           ("audit", f"{case_id}/audit.json", audit_bytes),
                                           ("stdout", f"{case_id}/stdout.txt", stdout_bytes),
                                           ("stderr", f"{case_id}/stderr.txt", b"")):
                        entry[f"{key}_path"], entry[f"{key}_sha256"] = rel, hashlib.sha256(data).hexdigest()
                    manifest["cases"].append(entry)
                manifest_path = result / "candidate_manifest.json"
                manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
                self.assertEqual(module.audit_bundle(manifest_path, target), [])
                raw_path = result / "control" / "raw.jsonl"
                raw_path.write_bytes(raw_path.read_bytes() + b'{"event":"runner_complete","exit_code":1}\n')
                errors = module.audit_bundle(manifest_path, target)
                self.assertTrue(any("digest mismatch" in error for error in errors), repr(errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
