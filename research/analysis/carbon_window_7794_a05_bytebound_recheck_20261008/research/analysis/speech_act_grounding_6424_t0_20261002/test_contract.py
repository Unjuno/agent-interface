import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("speech_act_candidate", Path(__file__).with_name("candidate.py"))
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)


class ContractTests(unittest.TestCase):
    def test_frozen_cases_match_the_independent_transition_contract(self):
        import json
        from pathlib import Path
        cases = json.loads((Path(__file__).parent / "cases.json").read_text())["cases"]
        rows = {row["case_id"]: row for row in map(candidate.decide, cases)}
        self.assertEqual(rows["direct"]["transition"], "EXECUTE_AFTER_ORDINARY_GATES")
        self.assertEqual(rows["indirect"]["transition"], "EXECUTE_AFTER_ORDINARY_GATES")
        self.assertEqual(rows["capability_question"]["transition"], "EXPLAIN")
        self.assertEqual(rows["quoted_third_party"]["transition"], "EXPLAIN")
        self.assertEqual(rows["prepare_only"]["transition"], "PREPARE")
        self.assertEqual(rows["explicit_negation"]["transition"], "EXPLAIN")
        self.assertEqual(rows["ambiguous_force"]["transition"], "ASK")
        self.assertEqual(rows["premise_false_or_unknown_control"]["transition"], "YIELD")

    def test_bad_source_span_fails_closed(self):
        import json
        from pathlib import Path
        case = json.loads((Path(__file__).parent / "cases.json").read_text())["cases"][0]
        case["source_spans"][0]["text"] = "Send the report"
        self.assertIn("SOURCE_SPAN_MISMATCH", candidate.decide(case)["errors"])

    def test_unauthenticated_user_turn_fails_closed(self):
        import json
        from pathlib import Path
        case = json.loads((Path(__file__).parent / "cases.json").read_text())["cases"][0]
        case["turns"][0]["authenticated"] = False
        self.assertIn("UNAUTHENTICATED_TURN", candidate.decide(case)["errors"])


if __name__ == "__main__":
    unittest.main()
