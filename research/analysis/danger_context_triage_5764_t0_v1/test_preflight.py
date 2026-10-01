import json
from pathlib import Path
import unittest

from run import build_raw


HERE = Path(__file__).resolve().parent


class PreflightTests(unittest.TestCase):
    def test_fixture_contains_four_novelty_effect_cells_and_heldout_states(self):
        stream = json.loads((HERE / "preaudit_stream.json").read_text(encoding="utf-8"))
        optional = [row for row in stream["events"] if not row["mandatory"]]
        cells = {(row["novelty"], row["effect"]) for row in optional
                 if row["effect"] in (0, 1)}
        self.assertEqual(cells, {(0, 0), (0, 1), (1, 0), (1, 1)})
        self.assertTrue(any(row["effect"] is None for row in optional))
        delayed = next(row for row in optional if row["event_id"] == "delayed-effect-01")
        self.assertGreater(delayed["effect_available_at"], stream["decision_time"])
        self.assertEqual(sum(bool(row["mandatory"]) for row in stream["events"]), 1)

    def test_candidate_raw_has_no_oracle_outcomes(self):
        raw = build_raw(HERE / "preaudit_stream.json")
        self.assertEqual(raw["population_size"], 12)
        self.assertEqual(raw["mandatory_event_ids"], ["hard-01"])
        self.assertNotIn("truth", json.dumps(raw).lower())

    def test_selector_process_does_not_open_sealed_outcome_file(self):
        source = (HERE / "run.py").read_text(encoding="utf-8")
        self.assertNotIn("sealed_outcomes", source)


if __name__ == "__main__":
    unittest.main()
