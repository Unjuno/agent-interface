import copy
import unittest

import reconcile


def fixture_inputs():
    v38 = {
        "completed_holds": [
            {
                "id": "decision-a",
                "step": 0,
                "requested_ms": 100,
                "owner_commanded_hold_lower_ms": 101.01068,
                "owner_commanded_hold_upper_ms": 129.390114,
                "bound_width_ms": 28.379434,
            }
        ],
        "interrupted_holds": [],
        "summary": {
            "completed_hold_count": 1,
            "interrupted_verified_count": 0,
            "requested_total_ms": 100,
            "owner_commanded_hold_total_lower_ms": 101.01068,
            "owner_commanded_hold_total_upper_ms": 129.390114,
            "overshoot_total_lower_ms": 1.01068,
            "overshoot_total_upper_ms": 29.390114,
            "median_overshoot_lower_ms": 1.01068,
            "median_overshoot_upper_ms": 29.390114,
            "overshoot_fraction_lower": 0.0101068,
            "overshoot_fraction_upper": 0.29390114,
        },
    }
    v39 = {
        "completed_holds": [
            {
                "id": "decision-b",
                "step": 1,
                "requested_ms": 200,
                "owner_commanded_hold_lower_ms": 250.1114,
                "owner_commanded_hold_upper_ms": 260.2224,
                "bound_width_ms": 10.111,
            }
        ],
        "interrupted_holds": [
            {
                "id": "decision-c",
                "step": 0,
                "requested_ms": 500,
                "keys": ["Down", "space"],
                "full_keyset_ack_ns": 1_000_000,
                "empty_verified_ns": 213579736,
                "ack_to_empty_verified_ms": 212.579736,
            }
        ],
        "summary": {
            "completed_hold_count": 1,
            "interrupted_verified_count": 1,
            "requested_total_ms": 200,
            "owner_commanded_hold_total_lower_ms": 250.1114,
            "owner_commanded_hold_total_upper_ms": 260.2224,
            "overshoot_total_lower_ms": 50.1114,
            "overshoot_total_upper_ms": 60.2224,
            "median_overshoot_lower_ms": 50.1114,
            "median_overshoot_upper_ms": 60.2224,
            "overshoot_fraction_lower": 0.250557,
            "overshoot_fraction_upper": 0.301112,
        },
    }
    table = {
        "schema": "map01-held-input-audited-table-transcription-v1",
        "allocation_id": "MAP01-HELD-INPUT-FULLTRACE-59-T0-20261002-01",
        "completed_holds": [
            {"trace": "v38", "decision_id": "decision-a", "step": 0, "requested_ms": 100, "lower_ms": 101.011, "upper_ms": 129.390, "interval_width_ms": 28.379},
            {"trace": "v39", "decision_id": "decision-b", "step": 1, "requested_ms": 200, "lower_ms": 250.111, "upper_ms": 260.222, "interval_width_ms": 10.111},
        ],
        "reported_exact_precision_summaries": {
            "v38": {
                "completed_holds": 1,
                "verified_interrupted_holds": 0,
                "requested_total_ms": 100,
                "owner_commanded_hold_total_lower_ms": 101.01068,
                "owner_commanded_hold_total_upper_ms": 129.390114,
                "overshoot_total_lower_ms": 1.01068,
                "overshoot_total_upper_ms": 29.390114,
                "median_overshoot_lower_ms": 1.01068,
                "median_overshoot_upper_ms": 29.390114,
            },
            "v39": {
                "completed_holds": 1,
                "verified_interrupted_holds": 1,
                "requested_total_ms": 200,
                "owner_commanded_hold_total_lower_ms": 250.1114,
                "owner_commanded_hold_total_upper_ms": 260.2224,
                "overshoot_total_lower_ms": 50.1114,
                "overshoot_total_upper_ms": 60.2224,
                "median_overshoot_lower_ms": 50.1114,
                "median_overshoot_upper_ms": 60.2224,
            },
        },
        "interrupted_hold": {
            "trace": "v39",
            "decision_id": "decision-c",
            "step": 0,
            "requested_ms": 500,
            "keys": ["Down", "space"],
            "full_keyset_ack_ns": 1_000_000,
            "empty_verified_ns": 213579736,
            "ack_to_empty_verified_ms": 212.579736,
            "classification": "interrupted_empty_verified",
            "excluded_from_completed_hold_totals": True,
        },
    }
    return v38, v39, table


class PriorTableReconciliationTests(unittest.TestCase):
    def test_matches_display_rows_and_exact_aggregates(self):
        result = reconcile.reconcile(*fixture_inputs(), expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "PASS_PRIOR_TABLE_RECONCILED")
        self.assertEqual(result["completed_rows_matched"], 2)
        self.assertEqual(result["errors"], [])

    def test_rejects_a_missing_prior_completed_row(self):
        v38, v39, table = fixture_inputs()
        table["completed_holds"].pop()
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")

    def test_rejects_row_value_beyond_frozen_display_precision(self):
        v38, v39, table = fixture_inputs()
        v38["completed_holds"][0]["owner_commanded_hold_lower_ms"] += 0.001
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")

    def test_rejects_aggregate_difference_above_one_nanosecond(self):
        v38, v39, table = fixture_inputs()
        table["reported_exact_precision_summaries"]["v39"]["owner_commanded_hold_total_lower_ms"] += 0.000000002
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")

    def test_rejects_interruption_receipt_mismatch(self):
        v38, v39, table = fixture_inputs()
        table["interrupted_hold"]["empty_verified_ns"] += 1
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")

    def test_rejects_duplicate_candidate_row_identity(self):
        v38, v39, table = fixture_inputs()
        v38["completed_holds"].append(copy.deepcopy(v38["completed_holds"][0]))
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")

    def test_rejects_non_finite_interruption_duration(self):
        v38, v39, table = fixture_inputs()
        v39["interrupted_holds"][0]["ack_to_empty_verified_ms"] = float("nan")
        result = reconcile.reconcile(v38, v39, table, expected_counts={"v38": 1, "v39": 1})
        self.assertEqual(result["disposition"], "FAIL_PRIOR_TABLE_RECONCILIATION")


if __name__ == "__main__":
    unittest.main()
