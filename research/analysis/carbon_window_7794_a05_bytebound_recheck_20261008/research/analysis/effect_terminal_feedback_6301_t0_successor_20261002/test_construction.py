import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import candidate
import auditor


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))

    def test_exact_predecessor_fixture_shape_and_identity(self):
        self.assertEqual(len(self.fixture["traces"]), 9)
        self.assertEqual(self.fixture["schema"], "6301-effect-terminal-feedback-v1")
        self.assertEqual([item["id"] for item in self.fixture["traces"]][5], "cancelled_input")

    def test_current_nonapplication_is_not_unknown(self):
        task = self.fixture["traces"][5]
        row = candidate.score_task(task)
        self.assertEqual(row["evidence"]["effect_status"], "NOT_APPLIED_VERIFIED")
        self.assertEqual(row["B_TYPED_EFFECT_PENDING"]["display"], "No target effect verified; task status follows obligations")
        self.assertEqual(row["evidence"]["task_terminal"], "PENDING")

    def test_stale_effect_becomes_unknown(self):
        task = self.fixture["traces"][8]
        self.assertEqual(candidate.score_task(task)["evidence"]["effect_status"], "UNKNOWN")

    def test_accepted_input_does_not_become_effect(self):
        task = self.fixture["traces"][2]
        self.assertTrue(task["effect"]["accepted_input"])
        self.assertEqual(candidate.score_task(task)["evidence"]["effect_status"], "UNKNOWN")

    def test_pending_obligations_prevent_terminal_success(self):
        for trace in self.fixture["traces"]:
            tasks = trace.get("tasks", [trace])
            for task in tasks:
                row = candidate.score_task(task)
                if any(x["required"] and x["status"] in candidate.PENDING for x in task["obligations"]):
                    self.assertEqual(row["evidence"]["task_terminal"], "PENDING")

    def test_candidate_and_oracle_reconstruct_all_task_and_display_records(self):
        output = candidate.build_result(self.fixture)
        self.assertEqual(auditor.verify(self.fixture, output), (10, 30))

    def test_all_frozen_semantic_mutations_are_rejected(self):
        output = candidate.build_result(self.fixture)
        controls = auditor.mutation_controls(self.fixture, output)
        self.assertEqual(len(controls), 4)
        self.assertTrue(all(control["rejected"] for control in controls), controls)

    def test_oracle_is_separately_authored(self):
        self.assertNotEqual(candidate.score_task.__code__.co_code, auditor.oracle_row.__code__.co_code)


if __name__ == "__main__":
    unittest.main()
