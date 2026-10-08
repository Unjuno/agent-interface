"""Pre-freeze construction and corruption controls for Issue #8624 T0 A01."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import auditor
import candidate


PACKAGE = Path(__file__).resolve().parent
MODEL = json.loads((PACKAGE / "model.json").read_text())


def frozen_record() -> dict:
    names = ("model.json", "candidate.py", "auditor.py")
    hashes = {
        name: hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
        for name in names
    }
    return {
        "allocation": "8624-T0-A02-20261009",
        "main_sha": "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385",
        "cube_scan_limit": 100000,
        "source_hashes": hashes,
    }


def case_by_id(model: dict, case_id: str) -> dict:
    return next(case for case in model["cases"] if case["id"] == case_id)


class ResponsibilityConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = frozen_record()
        cls.result = candidate.build_output(copy.deepcopy(MODEL), cls.freeze, PACKAGE)

    def test_monotone_control_recovers_support_cause_and_flip(self):
        row = next(r for r in self.result["cases"] if r["case_id"] == "monotone_positive_control")
        self.assertEqual(row["outcome"], 1)
        self.assertEqual(row["minimal_positive_supports"], [[0, 1]])
        self.assertEqual(row["robustness_radius"], 1)
        causes = row["prime_analysis"]["causal_results"]
        self.assertTrue(causes["visible"]["actual_cause"])
        self.assertEqual(causes["visible"]["minimum_contingency_size"], 0)

    def test_absent_prerequisite_is_a_signed_cause_with_contingency(self):
        row = next(r for r in self.result["cases"]
                   if r["case_id"] == "negative_absent_prerequisite_with_contingency")
        self.assertEqual(row["outcome"], 0)
        self.assertEqual(row["signed_facts"][0]["literal"], "!eligible")
        cause = row["prime_analysis"]["causal_results"]["eligible"]
        self.assertTrue(cause["actual_cause"])
        self.assertEqual(cause["minimum_contingency_size"], 1)
        self.assertIn(["reviewed"], cause["minimum_contingencies"])

    def test_positive_support_and_nearest_flip_summaries_do_not_identify_causes(self):
        left = next(r for r in self.result["cases"]
                    if r["case_id"] == "same_support_flip_different_responsibility")
        right = next(r for r in self.result["cases"]
                     if r["case_id"] == "same_support_flip_independent_response")
        self.assertEqual(left["minimal_positive_supports"], right["minimal_positive_supports"])
        self.assertEqual(left["minimal_outcome_flip_sets"], right["minimal_outcome_flip_sets"])
        self.assertEqual(left["minimal_positive_supports"], [[0]])
        self.assertEqual(left["minimal_outcome_flip_sets"], [[0]])
        self.assertEqual(left["prime_analysis"]["causal_results"]["q"]["minimum_contingency_size"], 2)
        self.assertFalse(right["prime_analysis"]["causal_results"]["q"]["actual_cause"])

    def test_robustness_radius_can_be_one_while_named_contingency_is_three(self):
        row = next(r for r in self.result["cases"]
                   if r["case_id"] == "unit_robustness_large_named_contingency")
        self.assertEqual(row["robustness_radius"], 1)
        self.assertEqual(
            row["prime_analysis"]["causal_results"]["s1"]["minimum_contingency_size"], 3)

    def test_dense_prime_family_refuses_without_silent_truncation(self):
        row = next(r for r in self.result["cases"]
                   if r["case_id"] == "dense_parity_complexity_control")
        self.assertGreater(row["prime_cube_scan_bound"], self.freeze["cube_scan_limit"])
        self.assertEqual(row["prime_analysis"]["status"], "UNKNOWN_TOO_LARGE")
        self.assertIsNone(row["prime_analysis"]["current_outcome_terms"])
        self.assertEqual(row["robustness_radius"], 1)

    def test_independent_raw_only_auditor_matches_exhaustive_oracle(self):
        report = auditor.audit(copy.deepcopy(MODEL), self.result, self.freeze, PACKAGE)
        self.assertEqual(report["status"], "PASS_METHOD_SCOPED", report["errors"])
        self.assertEqual(report["assignment_rows"], sum(
            1 << len(case["universe"]) for case in MODEL["cases"]))
        self.assertEqual(report["checks"]["paired_summaries_equal"], True)
        self.assertEqual(report["checks"]["paired_responsibility_differs"], True)

    def test_candidate_cli_returns_success_after_complete_json_output(self):
        with tempfile.TemporaryDirectory() as temp:
            freeze_path = Path(temp) / "FREEZE.json"
            freeze_path.write_text(json.dumps(self.freeze))
            argv = [str(PACKAGE / "candidate.py"), str(PACKAGE / "model.json"), str(freeze_path)]
            with mock.patch.object(sys, "argv", argv), redirect_stdout(StringIO()) as stdout:
                exit_code = candidate.main()
            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "CANDIDATE_COMPLETE")

    def test_auditor_cli_returns_success_for_completed_candidate_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            freeze_path = root / "FREEZE.json"
            raw_path = root / "candidate.raw.json"
            freeze_path.write_text(json.dumps(self.freeze))
            raw_path.write_text(json.dumps(self.result))
            argv = [
                str(PACKAGE / "auditor.py"),
                str(PACKAGE / "model.json"),
                str(raw_path),
                str(freeze_path),
            ]
            with mock.patch.object(sys, "argv", argv), redirect_stdout(StringIO()) as stdout:
                exit_code = auditor.main()
            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "PASS_METHOD_SCOPED")

    def test_reordering_stratified_rules_preserves_the_response(self):
        original = case_by_id(copy.deepcopy(MODEL), "negative_absent_prerequisite_with_contingency")
        reordered = copy.deepcopy(original)
        reordered["rules"].reverse()
        self.assertEqual(candidate.validate_case(original, "Goal"), [])
        self.assertEqual(candidate.validate_case(reordered, "Goal"), [])
        n = len(original["universe"])
        for mask in range(1 << n):
            state = candidate.assignment_for(mask, original["universe"])
            self.assertEqual(candidate.evaluate(original, "Goal", state),
                             candidate.evaluate(reordered, "Goal", state))

    def test_same_stratum_negative_dependency_is_rejected(self):
        malformed = case_by_id(copy.deepcopy(MODEL), "negative_absent_prerequisite_with_contingency")
        malformed["rules"][-1]["stratum"] = 1
        self.assertIn("negative_dependency_not_stratified:blocked",
                      candidate.validate_case(malformed, "Goal"))
        self.assertIn("negative_order_violation:blocked",
                      auditor.validate_rules(malformed, "Goal"))

    def test_fact_polarity_mutation_breaks_the_frozen_model_identity(self):
        mutated = copy.deepcopy(MODEL)
        case_by_id(mutated, "negative_absent_prerequisite_with_contingency")["observed"].append("reviewed")
        mutated_bytes = (json.dumps(mutated, indent=2) + "\n").encode()
        original_hash = hashlib.sha256((PACKAGE / "model.json").read_bytes()).hexdigest()
        self.assertNotEqual(
            hashlib.sha256(mutated_bytes).hexdigest(),
            original_hash,
        )

    def test_domain_omission_and_endpoint_mutations_are_detected(self):
        for mutation in ("omit_fact", "change_endpoint"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for name in ("candidate.py", "auditor.py"):
                    shutil.copy2(PACKAGE / name, root / name)
                altered = copy.deepcopy(MODEL)
                if mutation == "omit_fact":
                    case_by_id(altered, "negative_absent_prerequisite_with_contingency")["universe"].remove("reviewed")
                else:
                    altered["query_endpoint"] = "blocked"
                (root / "model.json").write_text(json.dumps(altered, sort_keys=True))
                report = auditor.audit(altered, self.result, self.freeze, root)
                self.assertEqual(report["status"], "FAIL")
                self.assertFalse(report["checks"]["frozen_hashes_match"])

    def test_corrupted_cause_output_is_rejected(self):
        corrupted = copy.deepcopy(self.result)
        target = next(r for r in corrupted["cases"]
                      if r["case_id"] == "same_support_flip_different_responsibility")
        target["prime_analysis"]["causal_results"]["q"]["minimum_contingency_size"] = 0
        report = auditor.audit(copy.deepcopy(MODEL), corrupted, self.freeze, PACKAGE)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("cause_mismatch", " ".join(report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
