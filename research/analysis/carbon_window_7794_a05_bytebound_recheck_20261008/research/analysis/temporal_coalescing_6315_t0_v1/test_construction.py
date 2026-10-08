import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec_c = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(candidate)
spec_a = importlib.util.spec_from_file_location("audit", ROOT / "audit.py")
audit = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(audit)
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class TestConstruction(unittest.TestCase):
    def test_projection_modes_are_deterministic_and_subsets(self):
        for case in FIXTURE["cases"]:
            for mode in case["modes"]:
                first = candidate.project(case, mode)
                self.assertEqual(first, candidate.project(case, mode))
                self.assertEqual(first, sorted(set(first)))
                self.assertTrue(all(0 <= i < len(case["rows"]) for i in first))

    def test_explicit_discriminators_and_unknown_controls(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture["mutations"] = []
        raw_records = []
        for case in fixture["cases"]:
            for mode in case["modes"]:
                raw_records.append({"case_id": case["case_id"], "mode": mode,
                                    "kept_indices": candidate.project(case, mode)})
        result = audit.audit(fixture, {"records": raw_records})
        self.assertEqual(result["case_mode_count"], 14)
        table = {(r["case_id"], r["mode"]): r for r in result["outcomes"]}
        self.assertEqual(table[("count_drop", "exact_full_stutter")]["verdict"], "NOT_PRESERVED")
        self.assertEqual(table[("deadline_drop", "exact_full_stutter")]["verdict"], "NOT_PRESERVED")
        self.assertEqual(table[("missing_time", "identity")]["verdict"], "UNKNOWN")
        self.assertEqual(table[("coverage_gap", "identity")]["verdict"], "UNKNOWN")
        self.assertEqual(table[("benign_stutter", "exact_full_stutter")]["verdict"], "PRESERVED")
        self.assertEqual(table[("deadline_control", "exact_full_stutter")]["verdict"], "PRESERVED")
        self.assertEqual(table[("deadline_control", "retain_critical_edges")]["verdict"], "PRESERVED")

    def test_mutations_reject_occurrence_time_coverage_and_mapping(self):
        raw = {"records": []}
        for case in FIXTURE["cases"]:
            for mode in case["modes"]:
                raw["records"].append({"case_id": case["case_id"], "mode": mode,
                                       "kept_indices": candidate.project(case, mode)})
        result = audit.audit(FIXTURE, raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertTrue(all(x["rejected"] for x in result["mutation_controls"]))


if __name__ == "__main__":
    unittest.main()
