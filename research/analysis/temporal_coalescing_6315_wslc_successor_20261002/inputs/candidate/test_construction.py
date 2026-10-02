import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
auditor_path = ROOT.parent / "auditor" / "auditor.py"
spec_a = importlib.util.spec_from_file_location("auditor", auditor_path)
auditor = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(auditor)


class ConstructionTests(unittest.TestCase):
    def test_candidate_deterministic_valid_mappings(self):
        for case in fixture["cases"]:
            for mode in case["modes"]:
                first = candidate.project(case, mode)
                self.assertEqual(first, candidate.project(case, mode))
                self.assertEqual(first, sorted(set(first)))
                self.assertTrue(all(type(i) is int and 0 <= i < len(case["rows"]) for i in first))

    def test_independent_truth_classes_and_coverage(self):
        rows = [{"ready": False, "t_ms": 0}, {"ready": True, "t_ms": 9},
                {"ready": False, "t_ms": 11}]
        event_case = {"coverage": "complete", "property": {"kind": "deadline_event", "deadline_ms": 10}, "rows": rows}
        self.assertTrue(auditor._truth(event_case, rows))
        self.assertFalse(auditor._truth(event_case, [rows[0], rows[2]]))
        self.assertIsNone(auditor._truth(event_case, [{"ready": True}]))
        incomplete = {"coverage": "unobserved", "property": {"kind": "deadline_ready", "deadline_ms": 10},
                      "rows": [{"ready": False, "t_ms": 0}, {"ready": True, "t_ms": 11}]}
        self.assertEqual(auditor._expected(incomplete, [0, 1])["verdict"], "UNKNOWN")

    def test_frozen_four_corruptions_rejected(self):
        records = [{"case_id": c["case_id"], "mode": mode,
                    "kept_indices": candidate.project(c, mode)}
                   for c in fixture["cases"] for mode in c["modes"]]
        raw = {"schema": "temporal-coalescing-candidate.v1", "records": records}
        result = auditor.audit(fixture, raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["case_mode_count"], 14)
        self.assertEqual(sum(x["rejected"] for x in result["mutation_controls"]), 4)


if __name__ == "__main__":
    unittest.main()
