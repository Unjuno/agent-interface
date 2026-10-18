"""Independent-oracle behavior and integrity mutation tests."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class PrincipalStratumAuditTests(unittest.TestCase):
    def test_independent_exhaustive_oracle_rejects_five_false_certificates(self):
        self.assertIsNotNone(importlib.util.find_spec("candidate"), "candidate.py is not implemented")
        self.assertIsNotNone(importlib.util.find_spec("auditor"), "auditor.py is not implemented")
        import auditor
        import candidate

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
        candidate_result = candidate.run(fixture)
        audit_result = auditor.audit(fixture, candidate_result, truth)

        self.assertEqual("PASS_METHOD_SCOPED", audit_result["disposition"])
        self.assertEqual(0, audit_result["reconstruction_errors"])
        self.assertEqual(5, audit_result["mutation_controls_rejected"])

        mutations = []
        wrong_bound = copy.deepcopy(candidate_result)
        wrong_bound["rows"][0]["policies"]["p0"]["always_demand_bounds"]["lower"] = "0"
        mutations.append(wrong_bound)

        assumed_monotonicity = copy.deepcopy(candidate_result)
        assumed_monotonicity["rows"][0]["assumptions_used"] = ["demand_monotonicity"]
        mutations.append(assumed_monotonicity)

        filled_undefined = copy.deepcopy(candidate_result)
        profiles = filled_undefined["rows"][0]["policies"]["p0"]["compatible_profiles"]
        undefined_unit = next(unit for profile in profiles for unit in profile if unit[4] is None)
        undefined_unit[4] = 0
        mutations.append(filled_undefined)

        omitted_completion = copy.deepcopy(candidate_result)
        omitted_completion["rows"][0]["policies"]["p0"]["compatible_profiles"].pop()
        mutations.append(omitted_completion)

        false_point = copy.deepcopy(candidate_result)
        false_point["rows"][0]["policies"]["p0"]["identification"] = "POINT_IDENTIFIED"
        mutations.append(false_point)

        for mutated in mutations:
            with self.assertRaises(ValueError):
                auditor.audit(fixture, mutated, truth)

        wrong_truth = copy.deepcopy(truth)
        wrong_truth["rows"][0]["expected_p0"]["lower"] = "0"
        with self.assertRaises(ValueError):
            auditor.audit(fixture, candidate_result, wrong_truth)

        wrong_input_digest = copy.deepcopy(candidate_result)
        wrong_input_digest["input_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            auditor.audit(fixture, wrong_input_digest, truth)

        undefined_as_zero = copy.deepcopy(fixture)
        undefined_as_zero["cases"][3]["recovery_successes"]["p0"]["A"] = 1
        with self.assertRaises(ValueError):
            candidate.run(undefined_as_zero)


if __name__ == "__main__":
    unittest.main()
