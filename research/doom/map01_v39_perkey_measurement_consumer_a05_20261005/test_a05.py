from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

import audit_a05

HERE = Path(__file__).resolve().parent
A04 = HERE / "SOURCE/A04"

def load_a04_audit():
    spec = importlib.util.spec_from_file_location("legacy_a04_audit", A04 / "audit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class InvocationCountTypeGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze, cls.raw, cls.result, oracle = audit_a05.verify_frozen_a04()
        cls.oracle = staticmethod(oracle)
        cls.legacy = load_a04_audit()

    def test_exact_integer_one_passes_successor(self):
        result = copy.deepcopy(self.result)
        result["candidate_invocations"] = 1
        self.assertEqual(
            audit_a05.audit_result(self.raw, result, self.oracle)["disposition"],
            "PASS_CLEANUP_CONSUMER_COMPOSITION_SCOPED")

    def test_legacy_accepts_boolean_but_successor_rejects_it(self):
        result = copy.deepcopy(self.result)
        result["candidate_invocations"] = True
        self.assertEqual(
            self.legacy.audit_result(self.raw, result, self.oracle)["disposition"],
            "PASS_CLEANUP_CONSUMER_COMPOSITION_SCOPED")
        with self.assertRaisesRegex(audit_a05.AuditFailure, "exact integer 1"):
            audit_a05.audit_result(self.raw, result, self.oracle)

    def test_successor_rejects_other_types_and_wrong_counts(self):
        for value in (False, 0, 2, 1.0, "1", None):
            result = copy.deepcopy(self.result)
            result["candidate_invocations"] = value
            with self.subTest(value=repr(value)):
                with self.assertRaises(audit_a05.AuditFailure):
                    audit_a05.audit_result(self.raw, result, self.oracle)

if __name__ == "__main__":
    unittest.main()
