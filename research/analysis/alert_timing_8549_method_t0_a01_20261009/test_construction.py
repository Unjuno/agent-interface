import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent
PROTOCOL = json.loads((ROOT / "protocol.json").read_text())
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class MethodConstructionTests(unittest.TestCase):
    def test_factorial_schedule_preserves_matched_presentation_fields(self):
        result = candidate.run(PROTOCOL, FIXTURE)
        self.assertEqual(len(result["factorial_trials"]), 24)
        by_cell = {}
        for block in range(1, 5):
            rows = [x for x in result["factorial_trials"] if x["block"] == block]
            self.assertEqual(len(rows), 6)
            self.assertEqual({(x["demand"], x["gap_ms"]) for x in rows},
                             {(d, g) for d in ("process", "task_irrelevant") for g in (250, 500, 2000)})
            expected_order = (("effect_complete_unverified", "authority_expiry_pending") if block % 2
                              else ("authority_expiry_pending", "effect_complete_unverified"))
            self.assertEqual({tuple(x["fact_ids"]) for x in rows}, {expected_order})
            self.assertTrue(all(x["salience"] == [5, 5] and x["visual_duration_ms"] == [1200, 1200]
                                and x["t2_deadline_ms"] == 3000 and x["event_count"] == 2 for x in rows))
            for row in rows:
                by_cell.setdefault((row["demand"], row["gap_ms"]), []).append(row)
        for cell_rows in by_cell.values():
            self.assertEqual(len({tuple(x["fact_ids"]) for x in cell_rows}), 2)
            self.assertEqual(len({x["event_positions"][0] for x in cell_rows}), 2)

    def test_control_arms_remain_outside_primary_factorial(self):
        result = candidate.run(PROTOCOL, FIXTURE)
        controls = {x["control"]: x for x in result["control_labels"]}
        self.assertEqual(set(controls), {"t2_only", "isolated_t1", "persistent_history"})
        self.assertEqual(controls["t2_only"]["available_event_ids"], ["E2"])
        self.assertEqual(controls["persistent_history"]["available_event_ids"], ["E1", "E2"])
        self.assertTrue(all(x["not_in_factorial"] for x in controls.values()))

    def test_synthetic_response_truth_key_and_mutations(self):
        result = candidate.run(PROTOCOL, FIXTURE)
        scores = result["response_scores"]
        self.assertEqual(len(scores), 6)
        self.assertEqual([x["correct_t2"] for x in scores], [True, False, False, False, False, False])
        self.assertEqual(auditor.inspect(result, PROTOCOL, FIXTURE), [])
        mutations, errors = auditor.mutations(result, PROTOCOL, FIXTURE)
        self.assertEqual(errors, [])
        self.assertEqual(len(mutations), 4)
        self.assertTrue(all(x["rejected"] for x in mutations))


if __name__ == "__main__":
    unittest.main()
