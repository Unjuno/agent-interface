import unittest

from policies import Resident, last_message, message_count


class CausalResidentTests(unittest.TestCase):
    def test_later_revoke_cannot_erase_prior_emission_and_releases(self):
        p = Resident()
        p.step({"kind": "obs", "id": "rise", "seq": 1, "gen": 1,
                "target": 1, "value": True})
        p.step({"kind": "revoke", "seq": 2, "gen": 1})
        self.assertEqual(p.actions, [("emit", "rise"), ("release", 1)])

    def test_revoke_before_observation_fails_closed(self):
        p = Resident()
        p.step({"kind": "revoke", "seq": 1, "gen": 1})
        p.step({"kind": "obs", "id": "late", "seq": 2, "gen": 1,
                "target": 1, "value": True})
        self.assertEqual(p.actions, [("release", 1), ("refuse", "late")])

    def test_replacement_rejects_old_generation_even_when_delayed(self):
        p = Resident()
        p.step({"kind": "replace", "seq": 3, "gen": 2, "target": 2})
        p.step({"kind": "obs", "id": "old", "seq": 2, "gen": 1,
                "target": 1, "value": True})
        self.assertEqual(p.actions[-1], ("refuse", "old"))

    def test_duplicate_event_id_is_still_a_second_message_arrival(self):
        events = [{"kind": "obs", "id": "x", "seq": 1, "value": True},
                  {"kind": "obs", "id": "x", "seq": 2, "value": True}]
        self.assertEqual(last_message(events), ["x"])
        self.assertEqual(message_count(events), ["x", "x"])

    def test_last_message_uses_arrival_order_not_sequence_sort(self):
        events = [{"kind": "obs", "id": "newer-seq", "seq": 3, "value": True},
                  {"kind": "obs", "id": "delayed-older", "seq": 2,
                   "value": False}]
        self.assertEqual(last_message(events), [])
        self.assertEqual(message_count(events), ["newer-seq"])


if __name__ == "__main__":
    unittest.main()
