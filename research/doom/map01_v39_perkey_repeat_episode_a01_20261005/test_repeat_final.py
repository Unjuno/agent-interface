"""Final mutation supplement, with assertion matching fail-closed precedence."""
import copy
import json
import unittest
from pathlib import Path
from candidate import reconstruct
from audit import audit_rows

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(x) for x in (HERE / "INPUT_EVENTS.jsonl").read_text().splitlines()]


class RepeatEpisodeFinalTests(unittest.TestCase):
    def test_raw_candidate_audit_agree_on_both_episodes(self):
        result = reconstruct(ROWS)
        self.assertEqual(result["episode_count"], 2)
        self.assertEqual(audit_rows(ROWS), result["episodes"])

    def test_duplicate_actuation_collapsing_episodes_is_refused(self):
        rows = copy.deepcopy(ROWS)
        first = rows[0]["physical_key_measurement"]["actuation_id"]
        for row in rows[2:]:
            row["physical_key_measurement"]["actuation_id"] = first
            row["physical_key_measurement"]["adapter_edge"]["actuation_id"] = first
        with self.assertRaisesRegex(ValueError, "distinct actuation"):
            reconstruct(rows)

    def test_incomplete_pair_is_refused(self):
        with self.assertRaises(ValueError): reconstruct(ROWS[:3])

    def test_mixed_outer_context_is_refused(self):
        rows = copy.deepcopy(ROWS)
        rows[2]["intent_token"] = "other"
        with self.assertRaises(ValueError): reconstruct(rows)

    def test_overlapping_key_episodes_are_refused(self):
        rows = copy.deepcopy(ROWS)
        m = rows[2]["physical_key_measurement"]
        prior_up = rows[1]["physical_key_measurement"]["adapter_edge"]["interval"][1]
        m["adapter_edge"]["interval"] = [prior_up, prior_up + 2]
        m["bracket"]["physical_down_interval"] = m["adapter_edge"]["interval"]
        with self.assertRaises(ValueError): reconstruct(rows)


if __name__ == "__main__": unittest.main(verbosity=2)
