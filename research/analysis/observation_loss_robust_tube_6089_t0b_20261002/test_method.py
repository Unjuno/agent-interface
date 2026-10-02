import json
import unittest
from copy import deepcopy
from pathlib import Path

import audit
import candidate


CASES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))["cases"]


class ErasureMethodTests(unittest.TestCase):
    def setUp(self):
        self.rows = candidate.run(CASES)
        self.by_id = {row["case_id"]: row for row in self.rows}

    def test_no_loss_recovers_original_horizon(self):
        row = self.by_id["zero_loss_recovers_base"]
        self.assertEqual(row["policy_c_loss_robust"]["selected_horizon"], row["base_no_loss_horizon"])

    def test_planted_unsafe_optimism_and_safe_alternatives(self):
        row = self.by_id["one_miss_planted_unsafe_optimism"]
        self.assertEqual(row["policy_a_optimistic"]["disposition"], "UNSAFE_OPTIMISTIC_EXTENSION")
        self.assertTrue(row["policy_b_release_on_absence"]["safe"])
        self.assertTrue(row["policy_c_loss_robust"]["safe_for_all_declared_patterns"])
        self.assertLess(row["policy_c_loss_robust"]["selected_horizon"], row["base_no_loss_horizon"])

    def test_stale_and_invalidated_sources_do_not_refresh_authority(self):
        stale = self.by_id["delayed_old_generation_is_erasure"]
        self.assertFalse(stale["policy_b_release_on_absence"]["receipt_was_usable"])
        self.assertEqual(stale["policy_b_release_on_absence"]["disposition"], "RELEASED_ON_ABSENT_OR_STALE")
        invalid = self.by_id["target_invalidated_while_waiting"]
        self.assertEqual(invalid["policy_c_loss_robust"]["selected_horizon"], 0)
        self.assertEqual(invalid["policy_c_loss_robust"]["disposition"], "YIELD_INVALIDATED_TARGET")

    def test_burst_bound_and_unsupported_bound(self):
        burst = self.by_id["two_miss_bounded_burst"]["policy_c_loss_robust"]
        self.assertTrue(burst["safe_for_all_declared_patterns"])
        beyond = self.by_id["loss_beyond_declared_bound_stress"]["policy_c_loss_robust"]
        self.assertEqual(beyond["actual_status"], "BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE")
        self.assertEqual(self.by_id["loss_beyond_declared_bound_stress"]["stress"]["disposition"], "OUT_OF_BOUND_NOT_CERTIFIED")
        unknown = self.by_id["unsupported_loss_bound_yields"]["policy_c_loss_robust"]
        self.assertEqual(unknown["disposition"], "HOLD_LOSS_BOUND_UNSUPPORTED")
        self.assertEqual(unknown["selected_horizon"], 0)

    def test_recursive_auditor_matches_candidate(self):
        self.assertEqual(audit.audit(CASES, self.rows), {"status": "PASS_METHOD_SCOPED", "rows": 7, "errors": []})

    def test_five_corruptions_are_rejected(self):
        mutations = []
        x = deepcopy(self.rows); x[0]["policy_c_loss_robust"]["selected_horizon"] += 1; mutations.append(x)
        x = deepcopy(self.rows); x[3]["policy_b_release_on_absence"]["receipt_was_usable"] = True; mutations.append(x)
        x = deepcopy(self.rows); x[0]["policy_c_loss_robust"]["selected_horizon"] = 0; mutations.append(x)
        x = deepcopy(self.rows); x[5]["policy_c_loss_robust"]["actual_status"] = "NO_LOSS_CONTROL"; mutations.append(x)
        x = deepcopy(self.rows); x.pop(); mutations.append(x)
        self.assertEqual(len(mutations), 5)
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertEqual(audit.audit(CASES, changed)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
