import copy
import unittest

import audit
import prepare


def fixture():
    seeds = (101, 103, 107)
    deck = prepare.build(seeds)
    base = {"fc1.weight": [[0.0] * 9 for _ in range(16)], "fc1.bias": [0.0] * 16,
            "fc2.weight": [[0.0] * 16 for _ in range(4)], "fc2.bias": [0.0] * 4}
    base_sha = audit.digest_object(base)
    runs = []
    for data in deck["seeds"]:
        arms = {}
        for arm in audit.ARMS:
            a = [[0.0] * 16 for _ in range(2)]
            b = [[0.0] * 2 for _ in range(4)]
            checkpoints = []
            gated = arm == "role_gated"
            for step in range(9):
                pa = [audit.predict(base, a, b, 0, row["features"], gated)
                      for row in data["splits"]["a_heldout"]]
                pb = [audit.predict(base, a, b, int(gated), row["features"], gated)
                      for row in data["splits"]["b_heldout"]]
                checkpoints.append({"update_index": step, "adapter_a": copy.deepcopy(a),
                                    "adapter_b": copy.deepcopy(b), "base_sha256": base_sha,
                                    "predictions_a": pa, "predictions_b": pb,
                                    "accuracy_a": {"correct": sum(p == r["label"] for p, r in zip(pa, data["splits"]["a_heldout"])), "total": 128},
                                    "accuracy_b": {"correct": sum(p == r["label"] for p, r in zip(pb, data["splits"]["b_heldout"])), "total": 128}})
            arms[arm] = {"checkpoints": checkpoints}
        a_all = {tuple(r["features"]) for r in data["splits"]["a_support"] + data["splits"]["a_heldout"]}
        b_all = {tuple(r["features"]) for r in data["splits"]["b_arrival"] + data["splits"]["b_heldout"]}
        data["cross_role_overlap_count"] = len(a_all & b_all)
        data["role_conflict_probe"] = {"features": [0] * 8, "a_label": 0, "b_label": 0}
        runs.append({"seed": data["seed"], "base_initial": base, "arms": arms,
                     "scope_cases": {
                         **{name: {**inputs, "decision": expected}
                            for (name, inputs), expected in zip(
                                audit.SCOPE_INPUTS.items(),
                                ("PROPOSE", "YIELD", "YIELD", "YIELD"), strict=True)},
                         "dispatch_count": 0}})
    raw = {"schema": "unjuno.needle.role-context-candidate.v1", "dataset_sha256": "fixture",
           "seeds": runs}
    return deck, raw, seeds


class IndependentRoleAuditTests(unittest.TestCase):
    def test_clean_raw_replays_with_quality_hold(self):
        deck, raw, seeds = fixture()
        result = audit.reconcile(deck, raw, seeds)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["disposition"], "HOLD_ROLE_ADAPTATION_QUALITY")

    def test_wrong_a_and_b_targets_rejected(self):
        deck, raw, seeds = fixture()
        changed = copy.deepcopy(deck)
        changed["seeds"][0]["splits"]["a_heldout"][0]["label"] = 1
        self.assertTrue(audit.check_dataset(changed, seeds))

    def test_unreported_cross_role_overlap_rejected(self):
        deck, _, seeds = fixture()
        deck["seeds"][0]["cross_role_overlap_count"] = 17
        self.assertTrue(audit.check_dataset(deck, seeds))

    def test_scope_inputs_are_independently_frozen_and_checked(self):
        deck, raw, seeds = fixture()
        changed = copy.deepcopy(raw)
        changed["seeds"][0]["scope_cases"]["fresh_known"]["fresh"] = False
        self.assertTrue(audit.reconcile(deck, changed, seeds)["errors"])
        changed = copy.deepcopy(deck)
        changed["seeds"][0]["splits"]["b_heldout"][0]["label"] ^= 1
        self.assertTrue(audit.check_dataset(changed, seeds))

    def test_missing_checkpoint_and_prediction_mutation_rejected(self):
        deck, raw, seeds = fixture()
        changed = copy.deepcopy(raw)
        changed["seeds"][0]["arms"]["role_gated"]["checkpoints"].pop()
        self.assertTrue(audit.reconcile(deck, changed, seeds)["errors"])
        changed = copy.deepcopy(raw)
        changed["seeds"][0]["arms"]["role_gated"]["checkpoints"][1]["predictions_b"][0] ^= 1
        self.assertTrue(audit.reconcile(deck, changed, seeds)["errors"])

    def test_role_gate_and_scope_corruption_rejected(self):
        deck, raw, seeds = fixture()
        self.assertEqual(audit.adapter_gate(0), 0)
        self.assertEqual(audit.adapter_gate(1), 1)
        changed = copy.deepcopy(raw)
        changed["seeds"][0]["scope_cases"]["stale_known"]["decision"] = "PROPOSE"
        self.assertTrue(audit.reconcile(deck, changed, seeds)["errors"])

    def test_all_frozen_mutation_controls_reject(self):
        deck, raw, seeds = fixture()
        cases = audit.mutation_controls(deck, raw, seeds)
        self.assertEqual(len(cases), 6)
        self.assertTrue(all(cases.values()), cases)


if __name__ == "__main__":
    unittest.main(verbosity=2)
