import json
import unittest
from copy import deepcopy
from pathlib import Path

import analyze


class AuditConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_dir = analyze.RUN
        cls.report = json.loads((cls.run_dir / "report.json").read_text())
        cls.events = analyze.load_jsonl(cls.run_dir / "runtime/events.jsonl")
        cls.protocol = analyze.load_jsonl(cls.run_dir / "planner-protocol.jsonl")
        cls.visual = json.loads((analyze.HERE / "VISUAL_READ.json").read_text())

    def derive(self):
        return analyze.derive(deepcopy(self.report), deepcopy(self.events), deepcopy(self.protocol), deepcopy(self.visual))

    def test_exact_trace_yields_hold_and_null_endpoints(self):
        result = self.derive()
        self.assertEqual(result["status"], "HOLD_NO_EFFECTIVE_INTERVENTION_BOUND_V39_CELL")
        self.assertEqual(result["first_observed_health_loss"]["sequence"], 76)
        self.assertAlmostEqual(result["request_to_first_loss_capture_ms"], 1474.923434)
        self.assertIsNone(result["t_gate_ns"])
        self.assertIsNone(result["t_effective_ns"])
        self.assertIsNone(result["t_harm_irreversible_ns"])

    def test_prompt_mutation_rejected(self):
        turn = next(row for row in self.protocol if row.get("observed_ns") == 55518341448372)
        altered = turn["message"]["params"]["input"][0]["text"].replace("health: 85", "health: 84")
        protocol = deepcopy(self.protocol)
        next(row for row in protocol if row.get("observed_ns") == 55518341448372)["message"]["params"]["input"][0]["text"] = altered
        with self.assertRaisesRegex(ValueError, "source health mismatch"):
            analyze.derive(deepcopy(self.report), deepcopy(self.events), protocol, deepcopy(self.visual))

    def test_missing_first_loss_event_rejected(self):
        events = [row for row in self.events if not (row.get("event") == "typed_observation" and row.get("sequence") == 76)]
        with self.assertRaisesRegex(ValueError, "selected exact observations incomplete"):
            analyze.derive(deepcopy(self.report), events, deepcopy(self.protocol), deepcopy(self.visual))

    def test_terminal_mutation_rejected(self):
        report = json.loads(json.dumps(self.report))
        report["decisions"][2]["final_action_admission"]["status"] = "ADMITTED"
        with self.assertRaisesRegex(ValueError, "selected turn terminal changed"):
            analyze.derive(report, self.events, self.protocol, self.visual)


if __name__ == "__main__":
    unittest.main()
