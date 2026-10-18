"""Mutation checks for repeated same-key episode reconstruction."""
import copy
import json
import unittest
from candidate import reconstruct
from audit import audit_rows

HERE = __import__("pathlib").Path(__file__).resolve().parent
ROWS = [json.loads(x) for x in (HERE / "INPUT_EVENTS.jsonl").read_text().splitlines()]


class RepeatEpisodeTests(unittest.TestCase):
    def test_two_same_key_episodes_join_by_actuation_identity(self):
        got = reconstruct(ROWS)
        self.assertEqual(got["episode_count"], 2)
        self.assertEqual(got["same_key"], "F8")
        self.assertEqual(len({e["actuation_id"] for e in got["episodes"]}), 2)
        self.assertEqual(audit_rows(ROWS), got["episodes"])
        self.assertFalse(got["authority_granted"])
        self.assertFalse(got["application_effect_observed"])

    def test_repeated_outer_identity_without_unique_actuation_fails_closed(self):
        rows = copy.deepcopy(ROWS)
        second_id = rows[2]["physical_key_measurement"]["actuation_id"]
        for row in rows[2:]:
            m = row["physical_key_measurement"]
            m["actuation_id"] = "duplicate-g1-F8"
            m["adapter_edge"]["actuation_id"] = "duplicate-g1-F8"
        with self.assertRaisesRegex(ValueError, "exactly two distinct actuation"):
            reconstruct(rows)

    def test_unpaired_second_release_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "exactly two down/up episodes"):
            reconstruct(ROWS[:3])

    def test_mixed_context_fails_closed(self):
        rows = copy.deepcopy(ROWS)
        rows[2]["intent_token"] = "different"
        with self.assertRaises(ValueError):
            reconstruct(rows)

    def test_overlapping_episode_brackets_fail_closed(self):
        rows = copy.deepcopy(ROWS)
        second_down = rows[2]["physical_key_measurement"]
        second_down["adapter_edge"]["interval"][0] = rows[1]["physical_key_measurement"]["adapter_edge"]["interval"][1]
        second_down["adapter_edge"]["interval"][1] += 2
        second_down["bracket"]["physical_down_interval"] = second_down["adapter_edge"]["interval"]
        with self.assertRaisesRegex(ValueError, "episode timing invalid|episodes overlap"):
            reconstruct(rows)


if __name__ == "__main__": unittest.main(verbosity=2)
