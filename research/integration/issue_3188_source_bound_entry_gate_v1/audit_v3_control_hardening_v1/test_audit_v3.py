#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1")
SOURCE_DIR = REPO_ROOT / "research/analysis/map01_matched_recovery_entry_gate_3008_v2"
RAW_PATH = REPO_ROOT / BASE / "results/formal-02/raw.json"
AUDITOR_PATH = REPO_ROOT / BASE / "audit_v3_control_hardening_v1/independent_audit_v3.py"

spec = importlib.util.spec_from_file_location("independent_audit_v3", AUDITOR_PATH)
assert spec and spec.loader
audit_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_v3)


class AuditV3ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_bytes = RAW_PATH.read_bytes()
        cls.raw_data = json.loads(cls.raw_bytes)

    def test_frozen_baseline_passes(self):
        result = audit_v3.audit(self.raw_bytes, SOURCE_DIR)
        self.assertEqual(result["status"], "PASS_AUDIT_V3", result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"], {
            "rows": 37, "vectors": 32, "authorize": 1, "current": "HOLD", "controls": 5,
        })

    def test_missing_receipt_control_is_bound_to_its_named_condition(self):
        changed = copy.deepcopy(self.raw_data)
        changed["controls"][0]["terminal_integrity"] = True
        changed["controls"][0]["arm_bound_audit"] = False
        errors = audit_v3.structure_errors(changed)
        self.assertIn("control identity/value/decision mismatch at 0", errors)

    def test_json_integer_zero_is_not_boolean_false(self):
        changed = copy.deepcopy(self.raw_data)
        changed["controls"][0]["terminal_integrity"] = 0
        errors = audit_v3.structure_errors(changed)
        self.assertIn("control Boolean type mismatch at 0", errors)

    def test_truth_table_value_mutation_is_rejected(self):
        changed = copy.deepcopy(self.raw_data)
        changed["vectors"][0]["physical_task_effect_endpoint"] = True
        errors = audit_v3.structure_errors(changed)
        self.assertTrue(any("vector" in error for error in errors), errors)

    def test_entrypoint_rejects_any_changed_formal_raw_bytes(self):
        changed = copy.deepcopy(self.raw_data)
        changed["controls"][0]["terminal_integrity"] = True
        changed["controls"][0]["arm_bound_audit"] = False
        result = audit_v3.audit(json.dumps(changed).encode("utf-8"), SOURCE_DIR)
        self.assertEqual(result["status"], "FAIL_AUDIT_V3")
        self.assertIn("formal raw SHA-256 mismatch", result["errors"])
        self.assertTrue(any("control" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
