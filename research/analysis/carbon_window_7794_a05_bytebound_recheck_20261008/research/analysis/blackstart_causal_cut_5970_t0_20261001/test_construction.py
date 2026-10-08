import json
import unittest
from pathlib import Path

from candidate import cut_status, decide, enumerate_cuts

HERE = Path(__file__).resolve().parent


class FrozenTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.spec["cases"]}

    def test_declared_dispositions_hold_for_every_trace(self):
        for case in self.spec["cases"]:
            with self.subTest(case=case["case_id"]):
                result = decide(case, self.spec["required_epoch"])
                self.assertEqual(case["expect"], result["cut_status"])

    def test_only_positive_control_confers_ready(self):
        for case in self.spec["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(case["case_id"] == "positive_same_epoch", decide(case, "e1")["ready"])

    def test_all_five_adversarial_cases_are_graph_only_false_ready(self):
        for case in self.spec["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertTrue(decide(case, "e1")["graph_only_ready"])

    def test_missing_parent_does_not_enumerate_as_complete_graph(self):
        self.assertIsNone(enumerate_cuts(self.cases["missing_causal_parent"]["events"]))

    def test_delayed_release_remains_an_in_flight_channel(self):
        case = self.cases["release_message_in_flight"]
        is_cut, in_flight, error = cut_status(case["events"], case["cut"])
        self.assertTrue(is_cut)
        self.assertEqual(1, in_flight)
        self.assertIsNone(error)

    def test_every_selected_cut_is_prefix_and_parent_closed(self):
        for case in self.spec["cases"]:
            if case["case_id"] == "missing_causal_parent":
                continue
            with self.subTest(case=case["case_id"]):
                is_cut, _, error = cut_status(case["events"], case["cut"])
                self.assertTrue(is_cut)
                self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
