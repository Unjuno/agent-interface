"""Corrected, separate mutation supplement; leaves frozen A01 tests untouched."""
import copy
import json
import unittest
from pathlib import Path
from candidate import reconstruct
from audit import audit_rows

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(x) for x in (HERE / "INPUT_EVENTS.jsonl").read_text().splitlines()]


class RepeatEpisodeSupplement(unittest.TestCase):
    def test_valid_repeated_key_pair_matches_independent_audit(self):
        result = reconstruct(ROWS)
        self.assertEqual(result["episode_count"], 2)
        self.assertEqual(audit_rows(ROWS), result["episodes"])

    def test_collapsing_second_episode_to_first_actuation_is_rejected(self):
        rows = copy.deepcopy(ROWS)
        first = rows[0]["physical_key_measurement"]["actuation_id"]
        for row in rows[2:]:
            m = row["physical_key_measurement"]
            m["actuation_id"] = first
            m["adapter_edge"]["actuation_id"] = first
        with self.assertRaisesRegex(ValueError, "exactly two edges"):
            reconstruct(rows)

    def test_mixed_context_is_rejected(self):
        rows = copy.deepcopy(ROWS)
        rows[2]["intent_token"] = "different"
        with self.assertRaises(ValueError): reconstruct(rows)

    def test_incomplete_episode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly two down/up episodes"):
            reconstruct(ROWS[:3])

    def test_overlapping_same_key_episodes_are_rejected(self):
        rows = copy.deepcopy(ROWS)
        second = rows[2]["physical_key_measurement"]
        first_up = rows[1]["physical_key_measurement"]["adapter_edge"]["interval"][1]
        second["adapter_edge"]["interval"] = [first_up, first_up + 2]
        second["bracket"]["physical_down_interval"] = second["adapter_edge"]["interval"]
        with self.assertRaises(ValueError): reconstruct(rows)


if __name__ == "__main__": unittest.main(verbosity=2)
