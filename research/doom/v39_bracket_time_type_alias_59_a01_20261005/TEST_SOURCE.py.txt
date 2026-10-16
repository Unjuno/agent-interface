import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE / "v39_bracket_time_type_alias_59_a01_20261005"
sys.path.insert(0, str(PACKAGE))
import run_a01


class BracketTimestampTypeAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        baseline_path = (PACKAGE.parent /
                         "v39_application_consumption_conflict_59_a01_20261005" /
                         "CANDIDATE_SOURCE.py.txt")
        baseline_source = baseline_path.read_text(encoding="utf-8")
        cls.base_projector = staticmethod(run_a01.load_projector(
            baseline_source, str(baseline_path)))
        source = (HERE / "map01_overlap_controller_v39.py").read_text(encoding="utf-8")
        cls.candidate_projector = staticmethod(run_a01.load_projector(source, "candidate"))

        template = [json.loads(line) for line in
                    (PACKAGE / "INPUT.jsonl").read_text().splitlines() if line]
        down = next(row for row in template if row.get("event") == "input_admission")
        up = next(row for row in template if row.get("event") == "input_release_measurement")
        run_a01.set_edge_interval(down, "down", 0, 1)
        run_a01.set_edge_interval(up, "up", 2, 3)
        cls.positive = json.loads(json.dumps(template))

    def test_coherent_integer_control_remains_paired(self):
        self.assertEqual(
            run_a01.project(self.candidate_projector, self.positive)["status"],
            "adapter_edge_brackets_paired")

    def assert_bool_alias_rejected(self, endpoint, replacement):
        events = json.loads(json.dumps(self.positive))
        bracket = events[0]["physical_key_measurement"]["bracket"]["physical_down_interval"]
        bracket[endpoint] = replacement
        result = run_a01.project(self.candidate_projector, events)
        self.assertEqual(result["status"], "adapter_edge_receipt_incomplete")
        self.assertIsNone(result["down_edge_interval_ns"])
        self.assertIsNone(result["up_edge_interval_ns"])

    def test_false_timestamp_cannot_alias_integer_zero(self):
        self.assert_bool_alias_rejected(0, False)

    def test_true_timestamp_cannot_alias_integer_one(self):
        self.assert_bool_alias_rejected(1, True)


if __name__ == "__main__":
    unittest.main()
