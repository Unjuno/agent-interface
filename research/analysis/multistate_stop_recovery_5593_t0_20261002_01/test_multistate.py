import copy
import json
import unittest

from audit import audit, reconstruct
from candidate import derive


class MultistateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as handle:
            cls.data = json.load(handle)

    def test_candidate_matches_independent_reconstruction(self):
        self.assertEqual(derive(self.data), reconstruct(self.data))

    def test_denominator_and_recovery_occupancy(self):
        out = reconstruct(self.data)
        self.assertTrue(all(sum(row["counts"].values()) == 5 for row in out["occupancy"]))
        self.assertEqual(out["occupancy"][2]["counts"], {"CENSORED": 1, "RECOVERING": 2, "RUNNING": 1, "TERMINAL_STOP": 1})

    def test_repeated_stop_recovery_retained(self):
        out = reconstruct(self.data)
        self.assertEqual(out["transitions"][3]["counts"], {"RECOVERING->SAFE_STOP": 1, "RUNNING->VERIFIED_SUCCESS": 1})

    def test_omitted_episode_rejected_by_frozen_n(self):
        data = copy.deepcopy(self.data)
        data["episodes"].pop()
        self.assertEqual(reconstruct(data)["launched_n"], 4)
        with self.assertRaises(ValueError):
            audit(self.data, derive(data))

    def test_omitted_recovery_event_rejected(self):
        data = copy.deepcopy(self.data)
        data["episodes"][0]["events"].pop(2)
        with self.assertRaisesRegex(ValueError, "illegal transition"):
            reconstruct(data)

    def test_absorbing_success_then_recovery_rejected(self):
        data = copy.deepcopy(self.data)
        data["episodes"][0]["events"].append({"tick": 5, "state": "RECOVERING"})
        with self.assertRaisesRegex(ValueError, "illegal transition"):
            reconstruct(data)

    def test_unknown_event_rejected(self):
        data = copy.deepcopy(self.data)
        data["episodes"][0]["events"][1]["state"] = "MAGIC"
        with self.assertRaisesRegex(ValueError, "unknown event/status"):
            reconstruct(data)

    def test_unknown_status_rejected(self):
        data = copy.deepcopy(self.data)
        data["episodes"][1]["events"][2]["state"] = "TERMINAL_MAYBE"
        with self.assertRaisesRegex(ValueError, "unknown event/status"):
            reconstruct(data)

    def test_duplicate_episode_id_rejected(self):
        data = copy.deepcopy(self.data)
        data["episodes"][1]["id"] = data["episodes"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate episode id"):
            reconstruct(data)

    def test_candidate_denominator_loss_rejected(self):
        result = derive(self.data)
        result["occupancy"][1]["counts"]["RUNNING"] -= 1
        with self.assertRaisesRegex(ValueError, "differs"):
            audit(self.data, result)

    def test_administrative_censor_is_distinct(self):
        out = reconstruct(self.data)
        self.assertEqual(out["occupancy"][2]["counts"]["CENSORED"], 1)
        self.assertEqual(out["occupancy"][2]["counts"].get("TERMINAL_STOP"), 1)


if __name__ == "__main__":
    unittest.main()
