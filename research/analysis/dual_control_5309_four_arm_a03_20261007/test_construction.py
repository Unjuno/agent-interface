#!/usr/bin/env python3
"""Pre-freeze construction controls; no full candidate/auditor allocation run."""
import json
import unittest
from pathlib import Path

import candidate
import auditor
from contracts_snapshot import ContractError, EffectOccurrence, ExecutionReceipt, ReleaseReceipt


ROOT = Path(__file__).resolve().parent


class ConstructionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())

    def test_heldout_symbol_permutations_remain_separating(self):
        for profile in self.fixture["primary_profiles"]:
            self.assertEqual(candidate.information_gain(profile, profile["open_action"]), 1.0)

    def test_equal_symbol_control_has_no_information_gain(self):
        profile = dict(self.fixture["primary_profiles"][0])
        profile["receipt_symbols"] = {state: "same" for state in profile["target_ids"]}
        self.assertEqual(candidate.information_gain(profile, profile["open_action"]), 0.0)

    def test_duplicate_event_identity_is_consumed_once(self):
        item = {"event_id": "same-event", "fresh": True, "symbol": "glyph-x"}
        self.assertEqual(candidate.unique_fresh_symbols([item, dict(item)]), ["glyph-x"])

    def test_stale_receipt_does_not_enter_belief(self):
        item = {"event_id": "old-event", "fresh": False, "symbol": "glyph-x"}
        self.assertEqual(candidate.unique_fresh_symbols([item]), [])

    def test_bounded_commit_releases_exact_key(self):
        events = candidate.emit_key_events("commit-amber", 1)
        self.assertEqual([item["kind"] for item in events], ["key_down", "key_up"])
        self.assertEqual(events[0]["key"], events[1]["key"])

    def test_non_input_probe_cannot_create_held_key(self):
        self.assertEqual(candidate.emit_key_events("probe-route", 1), [])

    def test_task_only_and_dual_receive_identical_admitted_task_actions(self):
        profile = self.fixture["primary_profiles"][0]
        rows = [candidate.simulate(profile, profile["target_ids"][0], "fresh", arm, self.fixture)
                for arm in ("TASK_ONLY", "DUAL_PURPOSE")]
        self.assertEqual(rows[0]["admitted_task_actions"], rows[1]["admitted_task_actions"])

    def test_primary_clean_arms_have_distinct_expected_first_actions(self):
        profile = self.fixture["primary_profiles"][0]
        first_actions = {}
        for arm in candidate.ARMS:
            row = candidate.simulate(profile, profile["target_ids"][0], "fresh", arm, self.fixture)
            first_actions[arm] = row["trace"][0]["action"] if row["trace"] else None
        self.assertEqual(first_actions["TASK_ONLY"], sorted(profile["commit_actions"].values())[0])
        self.assertEqual(first_actions["EXPLICIT_SAFE_PROBE"], profile["probe_action"])
        self.assertEqual(first_actions["DUAL_PURPOSE"], profile["open_action"])
        self.assertIsNone(first_actions["FAIL_CLOSED_UNKNOWN"])

    def test_stale_receipt_stops_before_target_specific_commit(self):
        profile = self.fixture["primary_profiles"][0]
        row = candidate.simulate(profile, profile["target_ids"][0], "stale", "DUAL_PURPOSE", self.fixture)
        self.assertEqual([step["action"] for step in row["trace"]], [profile["open_action"]])
        self.assertEqual(row["yield_reason"], "stale-or-ambiguous-receipt")

    def test_witness_loss_removes_dual_purpose_task_route(self):
        profile = next(p for p in self.fixture["controls"] if p["id"] == "witness-loss")
        row = candidate.simulate(profile, profile["target_ids"][0], "fresh", "DUAL_PURPOSE", self.fixture)
        self.assertEqual(row["trace"], [])

    def test_no_safe_path_yields_for_each_arm(self):
        profile = next(p for p in self.fixture["controls"] if p["id"] == "no-safe-path")
        for arm in candidate.ARMS:
            row = candidate.simulate(profile, profile["target_ids"][0], "fresh", arm, self.fixture)
            self.assertEqual(row["trace"], [])

    def test_pinned_execution_receipt_contract_accepts_synthetic_replay(self):
        release = ReleaseReceipt(observed_ns=20, verified=True, keys_down=(), buttons_down=())
        receipt = ExecutionReceipt("cmd", "receipt", "a" * 64, "synthetic-no-authority",
                                   1, "surface", 10, 20, 1, EffectOccurrence.NONE, release)
        self.assertTrue(receipt.release.released)

    def test_candidate_replays_an_action_into_the_pinned_runtime_schema(self):
        profile = self.fixture["primary_profiles"][0]
        row = candidate.execution_receipt(profile, profile["target_ids"][0], "DUAL_PURPOSE",
                                          profile["open_action"], 1, 0, 1)
        self.assertEqual(row["effect_occurrence"], "observed")
        self.assertEqual(row["release"], {"observed_ns": row["ended_ns"], "verified": True,
                                           "keys_down": [], "buttons_down": []})

    def test_pinned_release_contract_rejects_claimed_release_with_held_key(self):
        with self.assertRaises(ContractError):
            ReleaseReceipt(observed_ns=20, verified=True, keys_down=("A",), buttons_down=())

    def test_independent_oracle_expected_dual_trace_uses_task_action(self):
        profile = self.fixture["primary_profiles"][1]
        actions, reason = auditor.expected_actions(profile, profile["target_ids"][0], "fresh",
                                                    "DUAL_PURPOSE", self.fixture)
        self.assertEqual(actions, [profile["open_action"], profile["commit_actions"][profile["target_ids"][0]]])
        self.assertIsNone(reason)

    def test_independent_oracle_censors_stale_receipt_path(self):
        profile = self.fixture["primary_profiles"][0]
        actions, reason = auditor.expected_actions(profile, profile["target_ids"][0], "stale",
                                                    "DUAL_PURPOSE", self.fixture)
        self.assertEqual(actions, [profile["open_action"]])
        self.assertEqual(reason, "stale-or-ambiguous-receipt")

    def test_independent_oracle_duplicate_receipt_keeps_same_identity(self):
        profile = self.fixture["primary_profiles"][0]
        records = auditor.expected_receipts(profile, profile["target_ids"][0], "duplicate",
                                            profile["probe_action"], 1)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0], records[1])


if __name__ == "__main__":
    unittest.main()
