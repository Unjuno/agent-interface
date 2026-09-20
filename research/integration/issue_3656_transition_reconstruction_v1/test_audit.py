from __future__ import annotations

import json
import unittest
from pathlib import Path

from .audit import RAW_SHA256, audit


REPO = Path(__file__).resolve().parents[3]
RAW_PATH = REPO / "research/integration/issue_2499_readiness_successor_3652_v1/evidence/formal-01/result.json"


def load_raw() -> tuple[dict, bytes]:
    data = RAW_PATH.read_bytes()
    return json.loads(data), data


def refresh_event_hashes(raw: dict) -> None:
    import hashlib

    for seq, row in enumerate(raw["ledger"]):
        row["seq"] = seq
        payload = {key: value for key, value in row.items() if key != "hash"}
        row["hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    raw["event_count"] = len(raw["ledger"])


class IndependentTransitionAuditTests(unittest.TestCase):
    def test_frozen_raw_is_held_only_for_receipt_gaps(self) -> None:
        raw, data = load_raw()
        result = audit(raw, data)
        self.assertEqual(result["canonical_lf_raw_sha256"], RAW_SHA256)
        self.assertTrue(result["checkout_line_endings_normalized"])
        self.assertEqual(result["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["derived_transitions"]["focus_drift_and_refusal"], "PASS")
        self.assertEqual(result["derived_transitions"]["modal_transition_and_recovery"], "PASS")
        self.assertEqual(result["derived_transitions"]["geometry_transition_and_refusal"], "PASS")
        self.assertEqual(result["derived_transitions"]["window_replacement_and_refusal"], "HOLD")
        self.assertEqual(result["derived_transitions"]["return_to_earlier_app"], "HOLD")
        self.assertIn("geometry_input_emission_receipt_missing", result["evidence_gaps"])
        self.assertIn("input_emission_receipt_count_incomplete", result["evidence_gaps"])
        self.assertIn("old_window_absence_receipt_missing", result["evidence_gaps"])
        self.assertIn("return_active_window_receipt_missing_or_mismatch", result["evidence_gaps"])

    def test_runner_boolean_mutation_cannot_promote_a_hold(self) -> None:
        raw, _ = load_raw()
        raw["checks"] = [True] * 5
        self.assertEqual(audit(raw)["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")

    def test_runner_boolean_false_does_not_replace_raw_reconstruction(self) -> None:
        raw, _ = load_raw()
        raw["checks"] = [False] * 5
        result = audit(raw)
        self.assertEqual(result["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(result["derived_transitions"]["focus_drift_and_refusal"], "PASS")

    def test_event_reordering_is_rejected_even_with_fresh_hashes(self) -> None:
        raw, _ = load_raw()
        raw["ledger"][4], raw["ledger"][5] = raw["ledger"][5], raw["ledger"][4]
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "FAIL_AUDIT_RAW_INTEGRITY")
        self.assertIn("ledger_event_order_or_cardinality_mismatch", result["errors"])

    def test_extra_event_is_rejected_even_with_fresh_hashes(self) -> None:
        raw, _ = load_raw()
        extra = {"seq": 0, "kind": "unexpected_input", "input_emitted": True}
        raw["ledger"].insert(6, extra)
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "FAIL_AUDIT_RAW_INTEGRITY")
        self.assertIn("ledger_event_order_or_cardinality_mismatch", result["errors"])

    def test_operation_count_mismatch_is_rejected(self) -> None:
        raw, _ = load_raw()
        raw["input_operations"] = 2
        result = audit(raw)
        self.assertIn("input_operation_count_mismatch", result["errors"])

    def test_frozen_raw_digest_mismatch_is_rejected(self) -> None:
        raw, data = load_raw()
        result = audit(raw, data + b"\n")
        self.assertIn("frozen_raw_sha256_mismatch", result["errors"])

    def test_boolean_cannot_substitute_for_sequence_integer(self) -> None:
        raw, _ = load_raw()
        refresh_event_hashes(raw)
        raw["ledger"][0]["seq"] = False
        result = audit(raw)
        self.assertIn("event_sequence_mismatch:0", result["errors"])

    def test_invalid_final_role_identity_is_rejected(self) -> None:
        raw, _ = load_raw()
        raw["apps"]["chromium"]["identity"]["matches"][0]["raw"] = "WM_CLASS(STRING) = \"unknown\""
        result = audit(raw)
        self.assertIn("final_identity_not_exactly_one:chromium", result["errors"])

    def test_reused_process_identity_is_a_contradiction(self) -> None:
        raw, _ = load_raw()
        raw["ledger"][10]["new_pid"] = raw["ledger"][10]["old_pid"]
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "FAIL_AUDIT_RAW_INTEGRITY")
        self.assertIn("transition_receipt_contradicts_preregistered_outcome", result["errors"])

    def test_unresolved_process_group_is_rejected(self) -> None:
        raw, _ = load_raw()
        raw["cleanup_processes"][0]["remaining_pids"] = [999]
        raw["ledger"][-1]["processes"] = raw["cleanup_processes"]
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "FAIL_AUDIT_RAW_INTEGRITY")
        self.assertIn("cleanup_process_group_unreconciled", result["errors"])

    def test_missing_replacement_receipt_remains_hold_even_if_runner_claims_true(self) -> None:
        raw, _ = load_raw()
        raw["ledger"][10]["old_window_absent"] = False
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(result["derived_transitions"]["window_replacement_and_refusal"], "HOLD")

    def test_replacement_receipt_and_return_observation_enable_derived_checks(self) -> None:
        raw, _ = load_raw()
        raw["ledger"][8]["input_emitted"] = True
        raw["ledger"][10]["old_window_absent"] = True
        raw["ledger"][12]["active_window"] = raw["apps"]["calc"]["window"]
        refresh_event_hashes(raw)
        result = audit(raw)
        self.assertEqual(result["decision"], "PASS_AUDIT_RECONSTRUCTION_SCOPED")
        self.assertEqual(set(result["derived_transitions"].values()), {"PASS"})

    def test_boolean_cannot_substitute_for_integer_operation_count(self) -> None:
        raw, _ = load_raw()
        raw["input_operations"] = True
        result = audit(raw)
        self.assertIn("input_operation_count_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
