import unittest

from protocol import bind_intent, make_rows, simulate_bound


class ProtocolTests(unittest.TestCase):
    def test_disjoint_deterministic_splits(self):
        a = make_rows(4790119, "support", 32)
        self.assertEqual(a, make_rows(4790119, "support", 32))
        b = make_rows(4790127, "heldout", 64)
        self.assertTrue({x["case_id"] for x in a}.isdisjoint({x["case_id"] for x in b}))
        self.assertTrue({x["state"]["scope_id"] for x in a}.isdisjoint({x["state"]["scope_id"] for x in b}))
        self.assertTrue({x["task"] for x in a}.isdisjoint({x["task"] for x in b}))
        support_values = {x["intent"].get("value") for x in a if x["intent"]["op"] == "set"}
        heldout_values = {x["intent"].get("value") for x in b if x["intent"]["op"] == "set"}
        self.assertTrue(support_values.isdisjoint(heldout_values))
        self.assertEqual({x["intent"]["reason"] for x in a if x["intent"]["op"] == "yield"},
                         {"forbidden", "ambiguous", "stale_scope", "missing_evidence"})
        self.assertEqual({x["intent"]["op"] for x in b}, {"set", "save", "toggle", "yield", "no_action"})

    def test_identity_is_bound_from_state_only(self):
        row = make_rows(4790119, "support", 32)[0]
        result = bind_intent(row["intent"], row["state"], row["requested_generation"])
        self.assertEqual(result["arguments"]["scope_id"], row["state"]["scope_id"])
        self.assertEqual(result["arguments"]["generation"], row["state"]["generation"])

    def test_spoofed_identity_refused(self):
        row = make_rows(4790119, "support", 32)[0]
        forged = dict(row["intent"], scope_id="attacker", generation=-1)
        self.assertEqual(bind_intent(forged, row["state"], row["requested_generation"])["status"], "REJECT")

    def test_wrong_json_types_refused_without_exception(self):
        row = make_rows(4790119, "support", 32)[0]
        for intent in ({"op": "set", "field": [], "value": "x"},
                       {"op": "yield", "reason": []}, {"op": "toggle", "target": []}):
            self.assertEqual(bind_intent(intent, row["state"], row["requested_generation"])["status"], "REJECT")

    def test_simulator_models_only_local_in_memory_effects(self):
        row = make_rows(4790119, "support", 32)[0]
        bound = bind_intent(row["intent"], row["state"], row["requested_generation"])
        self.assertEqual(simulate_bound(bound, row["state"])["kind"], "staged")

    def test_stale_and_forbidden_refuse(self):
        row = make_rows(4790127, "heldout", 64)[54]
        self.assertEqual(row["intent"]["op"], "yield")
        bound = bind_intent({"op": "set", "field": "timezone", "value": "Etc/UTC"}, row["state"], row["requested_generation"])
        self.assertEqual(bound["status"], "REJECT")
        self.assertEqual(bound["reason"], "stale_scope")


if __name__ == "__main__":
    unittest.main()
