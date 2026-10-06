"""Characterization tests for the #7748 job-class eligibility boundary."""

from __future__ import annotations

import importlib.util
import copy
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PREDECESSOR_AUDITOR = (
    ROOT
    / "research"
    / "analysis"
    / "processor_demand_witness_7748_t0_20261005"
    / "auditor.py"
)
PACKAGE = Path(__file__).resolve().parent
CASES = json.loads((PACKAGE / "cases.json").read_text(encoding="utf-8"))["cases"]
EXPECTED = {
    "recognized_mixed_feasible": {
        "status": "ELIGIBLE",
        "control_feasible": True,
        "all_feasible": True,
    },
    "best_effort_joint_overload": {
        "status": "ELIGIBLE",
        "control_feasible": True,
        "all_feasible": False,
    },
    "unknown_safety_critical_overload": {"status": "HOLD_UNKNOWN_JOB_CLASS"},
    "near_miss_control_class": {"status": "HOLD_UNKNOWN_JOB_CLASS"},
    "missing_class": {"status": "HOLD_UNKNOWN_JOB_CLASS"},
    "null_class": {"status": "HOLD_UNKNOWN_JOB_CLASS"},
    "non_string_class": {"status": "HOLD_UNKNOWN_JOB_CLASS"},
}


def load_predecessor_auditor():
    spec = importlib.util.spec_from_file_location("predecessor_7748_auditor", PREDECESSOR_AUDITOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_successor_module(name):
    path = PACKAGE / f"{name}.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"successor_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UnknownJobClassCharacterization(unittest.TestCase):
    def test_predecessor_silently_omits_unknown_class_from_controls(self):
        case = next(c for c in CASES if c["id"] == "unknown_safety_critical_overload")
        result = load_predecessor_auditor()._classify(case)

        self.assertEqual(result["status"], "ELIGIBLE")
        self.assertTrue(result["control_demand"]["feasible"])
        self.assertFalse(result["all_demand"]["feasible"])

    def test_candidate_preserves_known_class_control_and_joint_scopes(self):
        candidate = load_successor_module("candidate")
        self.assertIsNotNone(candidate, "successor candidate is not implemented yet")
        for case in CASES:
            with self.subTest(case=case["id"]):
                self.assertEqual(candidate.classify(case), EXPECTED[case["id"]])

    def test_successor_holds_every_unknown_or_malformed_class(self):
        candidate = load_successor_module("candidate")
        self.assertIsNotNone(candidate, "successor candidate is not implemented yet")
        for case in CASES:
            with self.subTest(case=case["id"]):
                self.assertEqual(candidate.classify(case), EXPECTED[case["id"]])

    def test_independent_auditor_rejects_eligible_unknown_class_row(self):
        candidate = load_successor_module("candidate")
        auditor = load_successor_module("audit")
        self.assertIsNotNone(candidate, "successor candidate is not implemented yet")
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")

        raw = {
            "schema": "7748-class-enum-a01-raw-v1",
            "rows": [
                {"input": case, "result": candidate.classify(case)} for case in CASES
            ],
        }
        unknown = next(
            row for row in raw["rows"]
            if row["input"]["id"] == "unknown_safety_critical_overload"
        )
        unknown["result"] = {
            "status": "ELIGIBLE",
            "control_feasible": True,
            "all_feasible": False,
        }

        result = auditor.audit(raw, CASES)

        self.assertEqual(result["status"], "FAIL_AUDIT")
        self.assertIn("result:unknown_safety_critical_overload", result["errors"])

    def test_independent_audit_accepts_exact_fixture_and_rejects_omission(self):
        candidate = load_successor_module("candidate")
        auditor = load_successor_module("audit")
        self.assertIsNotNone(candidate, "successor candidate is not implemented yet")
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        raw = {
            "schema": "7748-class-enum-a01-raw-v1",
            "rows": [
                {"input": case, "result": candidate.classify(case)} for case in CASES
            ],
        }

        self.assertEqual(auditor.audit(raw, CASES)["status"], "PASS_CLASS_BOUNDARY_SCOPED")
        omitted = dict(raw)
        omitted["rows"] = raw["rows"][:-1]
        rejected = auditor.audit(omitted, CASES)
        self.assertEqual(rejected["status"], "FAIL_AUDIT")
        self.assertIn("missing:non_string_class", rejected["errors"])

    def test_independent_audit_rejects_post_candidate_class_substitution(self):
        candidate = load_successor_module("candidate")
        auditor = load_successor_module("audit")
        self.assertIsNotNone(candidate, "successor candidate is not implemented yet")
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        raw = {
            "schema": "7748-class-enum-a01-raw-v1",
            "rows": [
                {"input": case, "result": candidate.classify(case)} for case in CASES
            ],
        }
        corrupted = copy.deepcopy(raw)
        corrupted["rows"][0]["input"]["jobs"][0]["class"] = "safety_critical"

        rejected = auditor.audit(corrupted, CASES)

        self.assertEqual(rejected["status"], "FAIL_AUDIT")
        self.assertIn("input:recognized_mixed_feasible", rejected["errors"])


if __name__ == "__main__":
    unittest.main()
