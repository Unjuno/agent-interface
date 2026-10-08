from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


HERE = Path(__file__).parent
INPUTS = json.loads((HERE / "cases.json").read_text())
ORACLE = json.loads((HERE / "oracle.json").read_text())


class T0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.run(INPUTS)
        cls.result = audit.audit(cls.raw, INPUTS, ORACLE)

    def test_independent_replay_passes(self):
        self.assertEqual(self.result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(self.result["rows"], 14)
        self.assertEqual(self.result["errors"], [])

    def test_planted_crossover_and_null_control(self):
        self.assertTrue(self.result["slow_local_better"])
        self.assertTrue(self.result["fast_direct_better"])
        self.assertTrue(self.result["planted_crossover_detected"])
        self.assertTrue(self.result["no_crossover_control_consistent"])

    def test_action_opportunity_and_release_accounting(self):
        for record in self.raw["records"]:
            self.assertEqual(record["action_count"], INPUTS["horizon"])
            self.assertTrue(record["terminal_neutral"])
            self.assertEqual(record["release"]["requested_at_tick"], INPUTS["horizon"])
            self.assertTrue(record["release"]["terminal_neutral"])
            self.assertEqual(record["release"]["neutral_at_tick"] - INPUTS["horizon"], record["release_lag_ticks"])
            self.assertLessEqual(abs(record["release"]["residual_command_applied"]), INPUTS["action_limit"])
        self.assertEqual(next(r for r in self.raw["records"] if r["case_id"] == "C07" and r["route"] == "direct")["release_lag_ticks"], 0)
        self.assertEqual(next(r for r in self.raw["records"] if r["case_id"] == "C07" and r["route"] == "local_periodic")["release_lag_ticks"], 1)

    def test_unobservable_semantic_world_does_not_get_semantic_claim(self):
        record = next(r for r in self.raw["records"] if r["case_id"] == "C07")
        ordinary = next(r for r in self.raw["records"] if r["case_id"] == "C01")
        self.assertEqual(next(c for c in INPUTS["cases"] if c["id"] == "C07")["targets"], next(c for c in INPUTS["cases"] if c["id"] == "C01")["targets"])
        self.assertEqual(record["rows"], ordinary["rows"])
        self.assertNotIn("semantic_claim", record)
        self.assertTrue(self.result["semantic_swap_claim_absent"])

    def test_pooled_only_reading_would_hide_slow_stratum_loss(self):
        totals = self.result["matrix_error_totals"]["planted_crossover"]
        self.assertLess(totals["direct"], totals["local_periodic"])
        slow_local = next(r for r in self.raw["records"] if r["case_id"] == "C01" and r["route"] == "local_periodic")
        slow_direct = next(r for r in self.raw["records"] if r["case_id"] == "C01" and r["route"] == "direct")
        self.assertLess(slow_local["tracking_error_sum"], slow_direct["tracking_error_sum"])

    def test_timestamp_corruption_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["records"][0]["rows"][1]["tick"] = 77
        self.assertNotEqual(audit.audit(bad, INPUTS, ORACLE)["status"], "PASS_METHOD_SCOPED")

    def test_candidate_visible_case_ids_do_not_reveal_oracle_labels(self):
        self.assertEqual([case["id"] for case in INPUTS["cases"]], [f"C{i:02d}" for i in range(1, 8)])
        self.assertTrue(all(set(case) == {"id", "targets"} for case in INPUTS["cases"]))

    def test_release_receipt_corruption_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["records"][1]["release"]["neutral_at_tick"] = INPUTS["horizon"]
        self.assertNotEqual(audit.audit(bad, INPUTS, ORACLE)["status"], "PASS_METHOD_SCOPED")

    def test_omitted_reversal_rejected(self):
        bad = copy.deepcopy(self.raw)
        record = next(r for r in bad["records"] if r["case_id"] == "C02")
        record["rows"].pop(2)
        self.assertNotEqual(audit.audit(bad, INPUTS, ORACLE)["status"], "PASS_METHOD_SCOPED")

    def test_unsafe_input_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["records"][0]["rows"][0]["applied"] = INPUTS["action_limit"] + 1
        self.assertNotEqual(audit.audit(bad, INPUTS, ORACLE)["status"], "PASS_METHOD_SCOPED")

    def test_fabricated_effect_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["records"][0]["rows"][0]["position_after"] += 1
        self.assertNotEqual(audit.audit(bad, INPUTS, ORACLE)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
