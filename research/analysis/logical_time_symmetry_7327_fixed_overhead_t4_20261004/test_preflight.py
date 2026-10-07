import importlib.util
import json
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
T3 = HERE.parent / "logical_time_symmetry_7327_fixed_overhead_t3_20261004"
spec_module = importlib.util.spec_from_file_location("t3_candidate", T3 / "candidate.py")
candidate = importlib.util.module_from_spec(spec_module)
spec_module.loader.exec_module(candidate)
spec_module = importlib.util.spec_from_file_location("t3_audit", T3 / "audit.py")
audit = importlib.util.module_from_spec(spec_module)
spec_module.loader.exec_module(audit)


class T4Preflight(unittest.TestCase):
    spec = json.loads((HERE / "spec.json").read_text())
    factor = Fraction(spec["factor"])

    def test_homogeneous_trace_control(self):
        for case in self.spec["scenarios"]:
            row = candidate.run_case(case, self.factor)
            self.assertEqual(row["variants"]["baseline"]["trace"], row["variants"]["homogeneous"]["trace"])

    def test_nonzero_fixed_delay_changes_reachable_hazard_boundary(self):
        case = next(c for c in self.spec["scenarios"] if c["id"] == "nonzero_startup_reachable_hazard")
        variants = candidate.run_case(case, self.factor)["variants"]
        self.assertEqual(variants["baseline"]["trace"]["first_unsafe_normalized"],
                         variants["homogeneous"]["trace"]["first_unsafe_normalized"])
        self.assertNotEqual(variants["baseline"]["trace"]["first_unsafe_normalized"],
                            variants["fixed_startup"]["trace"]["first_unsafe_normalized"])

    def test_independent_oracle_and_mutations(self):
        raw = {"schema":"logical-time-fixed-overhead-raw-v1", "allocation":self.spec["allocation"],
               "rows":[candidate.run_case(case, self.factor) for case in self.spec["scenarios"]]}
        errors, checks = audit.run_audit(self.spec, raw)
        self.assertEqual(errors, [])
        self.assertTrue(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
