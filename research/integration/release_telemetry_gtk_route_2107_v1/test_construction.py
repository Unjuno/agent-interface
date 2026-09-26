import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from policy import choose
from schedule import schedule
from audit import audit_decision_trace


class PolicyConstructionTests(unittest.TestCase):
    def test_independent_audit_reconstructs_observation_wait_and_continue(self):
        row = {
            "owner_actions": [{"attempt": 1, "caller_returned_ns": 1_000,
                               "receipt_status": "VALID_RELEASE_RECEIPT"}],
            "retry_count": 0,
            "decision_trace": [
                {"at_ns": 1_000, "elapsed_ns": 0, "action": "QUERY",
                 "action_returned": True, "receipt_status": "VALID_RELEASE_RECEIPT",
                 "visible_state": None, "key_down": None, "retries": 0,
                 "consumed_observation_number": 1},
                {"at_ns": 1_400, "elapsed_ns": 399, "action": "WAIT",
                 "action_returned": True, "receipt_status": "VALID_RELEASE_RECEIPT",
                 "visible_state": "PENDING", "key_down": False, "retries": 0,
                 "wait_requested_ns": 1_500, "wait_completed_ns": 50_001_500,
                 "wait_requested_duration_ns": 50_000_000},
                {"at_ns": 50_002_000, "elapsed_ns": 50_000_999, "action": "QUERY",
                 "action_returned": True, "receipt_status": "VALID_RELEASE_RECEIPT",
                 "visible_state": None, "key_down": None, "retries": 0,
                 "consumed_observation_number": 2},
                {"at_ns": 50_007_000, "elapsed_ns": 50_005_999, "action": "CONTINUE",
                 "action_returned": True, "receipt_status": "VALID_RELEASE_RECEIPT",
                 "visible_state": "DONE", "key_down": False, "retries": 0},
            ],
        }
        observations = [
            {"query_number": 1, "capture_started_ns": 1_100, "capture_finished_ns": 1_200,
             "keymap": {"sampled_ns": 1_250, "down": False},
             "available_to_policy_ns": 1_300, "visible_state": "PENDING"},
            {"query_number": 2, "capture_started_ns": 50_003_000,
             "capture_finished_ns": 50_004_000,
             "keymap": {"sampled_ns": 50_005_000, "down": False},
             "available_to_policy_ns": 50_006_000, "visible_state": "DONE"},
        ]
        self.assertEqual(audit_decision_trace(row, observations), [])
        bad = [dict(item) for item in observations]
        bad[1] = dict(bad[1], available_to_policy_ns=50_008_000)
        self.assertIn("decision_observation_order_age_or_value_mismatch",
                      audit_decision_trace(row, bad))
        bad_trace = [dict(step) for step in row["decision_trace"]]
        bad_trace[0]["consumed_observation_number"] = 2
        self.assertIn("query_action_missing_prior_observation",
                      audit_decision_trace(dict(row, decision_trace=bad_trace), observations))
        bad_trace = [dict(step) for step in row["decision_trace"]]
        bad_trace[1]["wait_completed_ns"] = 50_001_499
        self.assertIn("wait_duration_out_of_policy_bound",
                      audit_decision_trace(dict(row, decision_trace=bad_trace), observations))

    def test_done_requires_fresh_key_up_for_every_receipt_state(self):
        for receipt in ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT", "UNKNOWN"):
            self.assertEqual(choose(action_returned=True, receipt_status=receipt,
                                    visible_state="DONE", key_down=False,
                                    elapsed_ns=1, retries=0), "CONTINUE")
            self.assertNotEqual(choose(action_returned=True, receipt_status=receipt,
                                       visible_state="DONE", key_down=True,
                                       elapsed_ns=1, retries=0), "CONTINUE")

    def test_receipt_status_does_not_change_decision(self):
        states = ((None, None, 0, 0), ("PENDING", False, 20_000_000, 0),
                  ("PENDING", False, 500_000_000, 0), ("PENDING", False, 1_000_000_000, 1))
        for visible, key_down, elapsed, retries in states:
            actions = {choose(action_returned=True, receipt_status=receipt,
                              visible_state=visible, key_down=key_down,
                              elapsed_ns=elapsed, retries=retries)
                       for receipt in ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT", "UNKNOWN")}
            self.assertEqual(len(actions), 1)

    def test_policy_uses_query_retry_and_abort_recovery_states(self):
        args = dict(action_returned=True, receipt_status="VALID_RELEASE_RECEIPT",
                    key_down=False, retries=0)
        self.assertEqual(choose(visible_state=None, elapsed_ns=0, **args), "QUERY")
        self.assertEqual(choose(visible_state="PENDING", elapsed_ns=10, **args), "WAIT")
        self.assertEqual(choose(visible_state="PENDING", elapsed_ns=500_000_000, **args), "RETRY")
        self.assertEqual(choose(action_returned=True, receipt_status="UNKNOWN", visible_state="PENDING",
                                key_down=False, elapsed_ns=1_000_000_000, retries=1), "ABORT")

    def test_action_return_must_precede_continuation(self):
        self.assertEqual(choose(action_returned=False, receipt_status="VALID_RELEASE_RECEIPT",
                                visible_state="DONE", key_down=False, elapsed_ns=1, retries=0), "WAIT")

    def test_matched_fixture_delays_are_identical_across_receipt_arms(self):
        rows = schedule("formal")
        self.assertEqual(len(rows), 56)
        for rep in range(1, 9):
            for scenario in ("before", "after"):
                matched = [row for row in rows
                           if row[4] == rep and row[1] == scenario]
                self.assertEqual(len(matched), 3)
                self.assertEqual(len({(row[2], row[3]) for row in matched}), 1)
                if scenario == "before":
                    self.assertEqual(matched[0][2], matched[0][3])
                else:
                    self.assertEqual(matched[0][3], 0)

    def test_retry_thresholds_and_safety_boundaries(self):
        base = dict(action_returned=True, receipt_status="UNKNOWN",
                    visible_state="PENDING", key_down=False)
        self.assertEqual(choose(elapsed_ns=499_999_999, retries=0, **base), "WAIT")
        self.assertEqual(choose(elapsed_ns=500_000_000, retries=0, **base), "RETRY")
        self.assertEqual(choose(elapsed_ns=999_999_999, retries=1, **base), "WAIT")
        self.assertEqual(choose(elapsed_ns=1_000_000_000, retries=1, **base), "ABORT")
        self.assertEqual(choose(elapsed_ns=2_000_000_000, retries=1,
                                visible_state="DONE", key_down=False, **{
                                    k: v for k, v in base.items() if k not in ("visible_state", "key_down")
                                }), "CONTINUE")


if __name__ == "__main__":
    unittest.main()
