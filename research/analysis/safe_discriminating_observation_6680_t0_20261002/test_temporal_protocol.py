import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import temporal_candidate
import temporal_auditor


def fixture():
    return {
        "schema": "safe-discriminating-observation-6680-temporal-fixture-v1",
        "target_trajectory": [{"tick": tick, "position": tick} for tick in range(5)],
        "predictor": {"intercept": 0, "velocity": 1},
        "alarm_threshold": 1,
        "max_probe_observations": 1,
        "probe": {"tick": 4, "admissible": True, "effectful": False, "extends_lease": False},
        "signature_recoveries": [
            {"source_age": 1, "residual": 1, "recovery": "reobserve"},
            {"source_age": 0, "residual": 1, "recovery": "reset"},
        ],
        "diagnostic_alarm_signatures": [{"source_age": 1, "residual": 1}],
        "policies": ["always_reobserve", "always_reset", "immediate_yield", "bounded_diagnose"],
        "cases": [
            {
                "id": "c01",
                "pre_probe_observation": {"source_tick": 2, "received_tick": 3, "position": 2},
                "probe_observation": {"source_tick": 3, "received_tick": 4, "position": 3, "admissible": True},
                "lease": {"id": "l01", "acquired_tick": 0, "held_input": "right", "release_requested_tick": 3, "release_receipt": {"lease_id": "l01", "tick": 3}},
            },
            {
                "id": "c02",
                "pre_probe_observation": {"source_tick": 2, "received_tick": 3, "position": 2},
                "probe_observation": {"source_tick": 4, "received_tick": 4, "position": 3, "admissible": True},
                "lease": {"id": "l02", "acquired_tick": 0, "held_input": "right", "release_requested_tick": 3, "release_receipt": {"lease_id": "l02", "tick": 3}},
            },
            {
                "id": "c03",
                "pre_probe_observation": {"source_tick": 2, "received_tick": 3, "position": 1},
                "probe_observation": {"source_tick": 3, "received_tick": 4, "position": 2, "admissible": True},
                "lease": {"id": "l03", "acquired_tick": 0, "held_input": "right", "release_requested_tick": 3, "release_receipt": {"lease_id": "l03", "tick": 3}},
            },
            {
                "id": "c04",
                "pre_probe_observation": {"source_tick": 2, "received_tick": 3, "position": 2},
                "probe_observation": {"source_tick": 3, "received_tick": 4, "position": 3, "admissible": False},
                "lease": {"id": "l04", "acquired_tick": 0, "held_input": "right", "release_requested_tick": 3, "release_receipt": {"lease_id": "l04", "tick": 3}},
            },
            {
                "id": "c05",
                "pre_probe_observation": {"source_tick": 2, "received_tick": 3, "position": 2},
                "probe_observation": {"source_tick": 4, "received_tick": 4, "position": 3, "admissible": True, "supported": False},
                "lease": {"id": "l05", "acquired_tick": 0, "held_input": "right", "release_requested_tick": 3, "release_receipt": {"lease_id": "l05", "tick": 3}},
            },
        ],
    }


def oracle():
    worlds = {
        "c01": ("observation_path", "reobserve"),
        "c02": ("dynamics", "reset"),
        "c03": ("mixed_unknown", None),
        "c04": ("observation_path", "reobserve"),
        "c05": ("unknown", None),
    }
    result = {}
    for case_id, (world, correct) in worlds.items():
        result[case_id] = {
            "world": world,
            "correct_recovery": correct,
            "effects": {
                "reobserve": {"useful": correct == "reobserve", "post_recovery_residual": 0 if correct == "reobserve" else 2},
                "reset": {"useful": correct == "reset", "post_recovery_residual": 0 if correct == "reset" else 2},
                "yield": {"useful": False, "post_recovery_residual": None},
            },
        }
    return {"schema": "safe-discriminating-observation-6680-temporal-oracle-v1", "worlds": result, "identifiable_case_ids": ["c01", "c02"], "required_release_before_probe": True}


class TemporalProtocolTests(unittest.TestCase):
    def test_saved_inputs_match_hand_checked_test_fixture(self):
        base = Path(__file__).parent
        saved_fixture = json.loads((base / "temporal_fixture.json").read_text())
        saved_oracle = json.loads((base / "temporal_oracle.json").read_text())
        self.assertEqual(saved_fixture, fixture())
        self.assertEqual(saved_oracle, oracle())

    def test_numeric_timestamped_probe_separates_identifiable_recovery_causes(self):
        rows = temporal_candidate.run(fixture())["rows"]
        decisions = {(row["case_id"], row["policy"]): row["action"] for row in rows}
        self.assertEqual(decisions[("c01", "bounded_diagnose")], "reobserve")
        self.assertEqual(decisions[("c02", "bounded_diagnose")], "reset")
        self.assertEqual(decisions[("c03", "bounded_diagnose")], "yield")
        counts = {(row["case_id"], row["policy"]): row["diagnostic_observations"] for row in rows}
        self.assertEqual(counts[("c03", "bounded_diagnose")], 0)

    def test_identifiable_cases_share_preprobe_evidence(self):
        data = fixture()
        observations = [next(c["pre_probe_observation"] for c in data["cases"] if c["id"] == cid) for cid in ("c01", "c02")]
        self.assertEqual(observations[0], observations[1])

    def test_no_policy_probes_or_recovers_before_matching_release_receipt(self):
        data = fixture()
        data["cases"][0]["lease"]["release_receipt"] = None
        rows = temporal_candidate.run(data)["rows"]
        self.assertTrue(all(row["action"] == "yield" and row["diagnostic_observations"] == 0 for row in rows if row["case_id"] == "c01"))

    def test_inconsistent_frozen_trajectory_and_predictor_fail_closed(self):
        data = fixture()
        data["target_trajectory"][4]["position"] = 99
        rows = temporal_candidate.run(data)["rows"]
        self.assertTrue(all(row["action"] == "yield" and row["diagnostic_observations"] == 0 for row in rows))

    def test_zero_observation_budget_prevents_reobserve_and_diagnosis(self):
        data = fixture()
        data["max_probe_observations"] = 0
        rows = temporal_candidate.run(data)["rows"]
        self.assertTrue(all(row["action"] != "reobserve" and row["diagnostic_observations"] == 0 for row in rows))

    def test_fixed_reobserve_arm_respects_ineligible_and_unsupported_probe(self):
        rows = temporal_candidate.run(fixture())["rows"]
        for case_id in ("c04", "c05"):
            row = next(r for r in rows if r["case_id"] == case_id and r["policy"] == "always_reobserve")
            self.assertEqual(row["action"], "yield")
            self.assertEqual(row["diagnostic_observations"], 0)
        audit = temporal_auditor.audit(temporal_candidate.run(fixture()), fixture(), oracle())
        self.assertEqual(audit["status"], "PASS_METHOD_SCOPED")

    def test_pre_alarm_source_time_after_receive_fails_closed(self):
        data = fixture()
        data["cases"][0]["pre_probe_observation"]["source_tick"] = 4
        rows = temporal_candidate.run(data)["rows"]
        self.assertTrue(all(row["action"] == "yield" and row["diagnostic_observations"] == 0 for row in rows if row["case_id"] == "c01"))

    def test_probe_observation_outside_frozen_tick_is_not_consumed(self):
        data = fixture()
        data["cases"][0]["probe_observation"]["received_tick"] = 5
        rows = temporal_candidate.run(data)["rows"]
        bounded = next(row for row in rows if row["case_id"] == "c01" and row["policy"] == "bounded_diagnose")
        self.assertEqual((bounded["action"], bounded["diagnostic_observations"]), ("yield", 0))

    def test_independent_effect_oracle_audits_both_wrong_recovery_and_next_residual(self):
        raw = temporal_candidate.run(fixture())
        audit = temporal_auditor.audit(raw, fixture(), oracle())
        self.assertEqual(audit["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(audit["identifiable_counts"]["bounded_diagnose_wrong_recoveries"], 0)
        self.assertEqual(audit["identifiable_counts"]["bounded_diagnose_repeated_residuals"], 0)
        self.assertEqual(audit["identifiable_counts"]["always_reobserve_repeated_residuals"], 1)
        self.assertEqual(audit["identifiable_counts"]["always_reset_repeated_residuals"], 1)
        self.assertEqual(audit["identifiable_counts"]["immediate_yield_useful_effects"], 0)

    def test_corrupted_lease_order_is_rejected_by_raw_audit(self):
        raw = temporal_candidate.run(fixture())
        raw["rows"][0]["release_receipt_tick"] = 5
        audit = temporal_auditor.audit(raw, fixture(), oracle())
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertTrue(any("release" in error for error in audit["errors"]))

    def test_corrupted_effect_oracle_fails_policy_gate(self):
        damaged = oracle()
        damaged["worlds"]["c01"]["correct_recovery"] = "reset"
        audit = temporal_auditor.audit(temporal_candidate.run(fixture()), fixture(), damaged)
        self.assertEqual(audit["status"], "FAIL_AUDIT")

    def test_swapped_signature_recovery_labels_fail_effect_gate(self):
        data = fixture()
        data["signature_recoveries"][0]["recovery"], data["signature_recoveries"][1]["recovery"] = "reset", "reobserve"
        audit = temporal_auditor.audit(temporal_candidate.run(data), data, oracle())
        self.assertEqual(audit["status"], "FAIL_AUDIT")

    def test_recurrence_gate_fails_when_diagnosis_is_not_better_than_fixed_arms(self):
        damaged = oracle()
        damaged["worlds"]["c01"]["effects"]["reobserve"]["post_recovery_residual"] = 2
        audit = temporal_auditor.audit(temporal_candidate.run(fixture()), fixture(), damaged)
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertTrue(any("post-recovery residual" in error for error in audit["errors"]))

    def test_auditor_cli_persists_independent_raw_only_report(self):
        base = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "raw.json"
            audit_path = Path(directory) / "audit.json"
            raw_path.write_text(json.dumps(temporal_candidate.run(fixture())))
            result = subprocess.run(
                [sys.executable, str(base / "temporal_auditor.py"), str(raw_path), str(audit_path)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            saved = json.loads(audit_path.read_text())
            self.assertEqual(saved["status"], "PASS_METHOD_SCOPED")
            self.assertEqual(saved["rows"], 20)


if __name__ == "__main__":
    unittest.main()
