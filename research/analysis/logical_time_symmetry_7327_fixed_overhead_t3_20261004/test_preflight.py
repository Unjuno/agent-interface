import importlib.util
import json
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
for name in ("candidate", "audit"):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()[name] = module


class FixedOverheadPreflight(unittest.TestCase):
    spec = json.loads((HERE / "spec.json").read_text())
    factor = Fraction(spec["factor"])

    def test_homogeneous_scaling_preserves_normalized_trace(self):
        row = candidate.run_case(self.spec["scenarios"][1], self.factor)
        self.assertEqual(row["variants"]["baseline"]["trace"], row["variants"]["homogeneous"]["trace"])

    def test_nonzero_fixed_delay_moves_reachable_reaction(self):
        row = candidate.run_case(self.spec["scenarios"][1], self.factor)
        v = row["variants"]
        self.assertNotEqual(v["baseline"]["trace"]["first_unsafe_normalized"],
                            v["fixed_startup"]["trace"]["first_unsafe_normalized"])

    def test_zero_fixed_delay_remains_unobservable(self):
        row = candidate.run_case(self.spec["scenarios"][0], self.factor)
        self.assertEqual(row["variants"]["baseline"]["trace"],
                         row["variants"]["fixed_startup"]["trace"])

    def test_independent_oracle_reconstructs_candidate(self):
        raw = {"schema": "logical-time-fixed-overhead-raw-v1", "allocation": self.spec["allocation"],
               "rows": [candidate.run_case(case, self.factor) for case in self.spec["scenarios"]]}
        self.assertEqual(audit.integrity_errors(self.spec, raw), [])
        self.assertTrue(all(audit.scientific_checks(self.spec, raw).values()))


if __name__ == "__main__":
    unittest.main()
