import copy
import json
import unittest

from audit import audit, reconstruct
from candidate import derive


class RosterBoundMultistateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as f: cls.data = json.load(f)
        with open("frozen_roster.json", encoding="utf-8") as f: cls.roster = json.load(f)

    def test_candidate_matches_raw_audit(self):
        self.assertEqual(derive(self.data), reconstruct(self.data, self.roster))

    def test_all_tick_occupancy_equals_frozen_n(self):
        out = reconstruct(self.data, self.roster)
        self.assertTrue(all(sum(row["counts"].values()) == 6 for row in out["occupancy"]))

    def test_stop_and_recovery_remain_nonterminal(self):
        out = reconstruct(self.data, self.roster)
        self.assertEqual(out["occupancy"][2]["counts"]["RECOVERING"], 2)
        self.assertEqual(out["transitions"][3]["counts"]["RECOVERING->SAFE_STOP"], 1)

    def test_censor_and_terminal_stop_are_distinct(self):
        counts = reconstruct(self.data, self.roster)["occupancy"][2]["counts"]
        self.assertEqual(counts["CENSORED"], 1)
        self.assertEqual(counts["TERMINAL_STOP"], 1)

    def test_omitted_episode_rejected_by_frozen_roster(self):
        data = copy.deepcopy(self.data); data["episodes"].pop()
        with self.assertRaisesRegex(ValueError, "frozen launch roster"):
            reconstruct(data, self.roster)

    def test_omitted_recovery_rejected(self):
        data = copy.deepcopy(self.data); data["episodes"][0]["events"].pop(2)
        with self.assertRaisesRegex(ValueError, "illegal transition"):
            reconstruct(data, self.roster)

    def test_absorbing_state_rejects_recovery(self):
        data = copy.deepcopy(self.data); data["episodes"][0]["events"].append({"tick": 5, "state": "RECOVERING"})
        with self.assertRaisesRegex(ValueError, "illegal transition"):
            reconstruct(data, self.roster)

    def test_unknown_state_rejected(self):
        data = copy.deepcopy(self.data); data["episodes"][1]["events"][2]["state"] = "TERMINAL_MAYBE"
        with self.assertRaisesRegex(ValueError, "unknown event/status"):
            reconstruct(data, self.roster)

    def test_duplicate_id_rejected(self):
        data = copy.deepcopy(self.data); data["episodes"][1]["id"] = data["episodes"][0]["id"]
        with self.assertRaisesRegex(ValueError, "frozen launch roster"):
            reconstruct(data, self.roster)

    def test_denominator_mutation_rejected(self):
        output = derive(self.data); output["launched_n"] -= 1
        with self.assertRaisesRegex(ValueError, "differs"):
            audit(self.data, self.roster, output)

    def test_wrong_allocation_rejected(self):
        data = copy.deepcopy(self.data); data["allocation"] = "other"
        with self.assertRaisesRegex(ValueError, "allocation mismatch"):
            reconstruct(data, self.roster)


if __name__ == "__main__": unittest.main()
