import json
import tempfile
import unittest
from pathlib import Path

from audit import audit
from simulate import POLICIES, SCENARIOS, make_group


class CanaryDetectionTests(unittest.TestCase):
    def test_in_deck_shift_between_blocks_is_caught(self):
        row = make_group("hidden_in_deck_between", "bracketed_canary")
        self.assertEqual(row["candidate_disposition"], "HOLD_BEHAVIOR_SHIFT_BEFORE_B")

    def test_mid_block_shift_holds_whole_block(self):
        row = make_group("hidden_in_deck_mid_B", "bracketed_canary")
        self.assertEqual(row["candidate_disposition"], "HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT")
        self.assertEqual(len(row["route_rows"]["B"]), 200)

    def test_out_of_deck_clean_canary_never_proves_stability(self):
        row = make_group("hidden_outside_deck_between", "bracketed_canary")
        self.assertEqual(row["candidate_disposition"],
                         "NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED")
        self.assertTrue(row["evaluator_truth"]["semantic_shift"])

    def test_schema_context_and_snapshot_controls_are_not_model_shift(self):
        expected = {
            "schema_only": "HOLD_SCHEMA_CHANGE",
            "prompt_context_drift": "HOLD_PROMPT_CONTEXT_DRIFT",
            "visible_snapshot_change": "HOLD_SNAPSHOT_CHANGED",
        }
        for scenario, disposition in expected.items():
            with self.subTest(scenario=scenario):
                row = make_group(scenario, "bracketed_canary")
                self.assertEqual(row["candidate_disposition"], disposition)

    def test_alias_and_metadata_baselines_do_not_claim_behavior_verified(self):
        for scenario in SCENARIOS:
            alias = make_group(scenario, "alias_only")
            metadata = make_group(scenario, "metadata_only")
            self.assertIn("MODEL_BEHAVIOR_UNVERIFIED", alias["candidate_disposition"])
            self.assertTrue(metadata["candidate_disposition"].startswith((
                "NO_METADATA_CHANGE", "HOLD_")))

    def test_independent_auditor_accepts_all_frozen_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.jsonl"
            path.write_text("".join(json.dumps(make_group(s, p), sort_keys=True,
                                                   separators=(",", ":")) + "\n"
                                for s in SCENARIOS for p in POLICIES), encoding="utf-8")
            result = audit(str(path))
        self.assertEqual(result["verdict"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["n_groups"], 21)

    def test_auditor_rejects_candidate_disposition_tamper(self):
        rows = [make_group(s, p) for s in SCENARIOS for p in POLICIES]
        rows[1]["candidate_disposition"] = "MODEL_STABLE_PROVEN"
        result = self.audit_rows(rows)
        self.assertEqual(result["verdict"], "FAIL_AUDIT")

    def test_auditor_rejects_missing_route_attempt(self):
        rows = [make_group(s, p) for s in SCENARIOS for p in POLICIES]
        rows[0]["route_rows"]["B"].pop()
        result = self.audit_rows(rows)
        self.assertEqual(result["verdict"], "FAIL_AUDIT")

    def test_auditor_rejects_oracle_truth_tamper(self):
        rows = [make_group(s, p) for s in SCENARIOS for p in POLICIES]
        rows[-1]["evaluator_truth"]["semantic_shift"] = False
        result = self.audit_rows(rows)
        self.assertEqual(result["verdict"], "FAIL_AUDIT")

    @staticmethod
    def audit_rows(rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.jsonl"
            path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                                       for row in rows), encoding="utf-8")
            return audit(str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
