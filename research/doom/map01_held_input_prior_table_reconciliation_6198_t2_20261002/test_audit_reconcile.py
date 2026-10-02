import unittest

from audit_reconcile import reconcile


def fixture():
    def row(name, ident, step, req, low, high):
        return {"id": ident, "step": step, "requested_ms": req, "keys": ["space"],
                "owner_commanded_hold_lower_ms": low, "owner_commanded_hold_upper_ms": high,
                "overshoot_lower_ms": low - req, "overshoot_upper_ms": high - req,
                "bound_width_ms": high - low, "classification": "ordinary_completed_bounded"}

    def summary(rows, interrupted):
        requested = sum(r["requested_ms"] for r in rows)
        lo = sum(r["owner_commanded_hold_lower_ms"] for r in rows)
        hi = sum(r["owner_commanded_hold_upper_ms"] for r in rows)
        olo = sum(r["overshoot_lower_ms"] for r in rows)
        ohi = sum(r["overshoot_upper_ms"] for r in rows)
        from statistics import median
        return {"completed_hold_count": len(rows), "interrupted_verified_count": interrupted,
                "requested_total_ms": requested, "owner_commanded_hold_total_lower_ms": lo,
                "owner_commanded_hold_total_upper_ms": hi, "overshoot_total_lower_ms": olo,
                "overshoot_total_upper_ms": ohi, "median_overshoot_lower_ms": median([x["overshoot_lower_ms"] for x in rows]),
                "median_overshoot_upper_ms": median([x["overshoot_upper_ms"] for x in rows]),
                "overshoot_fraction_lower": olo / requested, "overshoot_fraction_upper": ohi / requested}

    v38_rows = [row("v38", "a", 0, 10, 11.1, 12.2)]
    v39_rows = [row("v39", "b", 1, 20, 21.1, 22.4)]
    interrupted = {"id": "c", "step": 0, "requested_ms": 5, "keys": ["Down"],
                   "full_keyset_ack_ns": 100, "empty_verified_ns": 200,
                   "ack_to_empty_verified_ms": 0.0001, "classification": "interrupted_empty_verified"}
    v38 = {"completed_holds": v38_rows, "interrupted_holds": [], "summary": summary(v38_rows, 0)}
    v39 = {"completed_holds": v39_rows, "interrupted_holds": [interrupted], "summary": summary(v39_rows, 1)}
    table = {"completed_holds": [
        {"trace": "v38", "decision_id": "a", "step": 0, "requested_ms": 10, "keys": ["space"],
         "lower_ms": 11.1, "upper_ms": 12.2, "interval_width_ms": 1.1},
        {"trace": "v39", "decision_id": "b", "step": 1, "requested_ms": 20, "keys": ["space"],
         "lower_ms": 21.1, "upper_ms": 22.4, "interval_width_ms": 1.3}],
        "interrupted_hold": {"trace": "v39", "decision_id": "c", **{k: v for k, v in interrupted.items() if k != "id"},
                             "excluded_from_completed_hold_totals": True},
        "reported_exact_precision_summaries": {
            "v38": {"completed_holds": 1, "verified_interrupted_holds": 0, **summary(v38_rows, 0)},
            "v39": {"completed_holds": 1, "verified_interrupted_holds": 1, **summary(v39_rows, 1)}}}
    return v38, v39, table


class ReconciliationTests(unittest.TestCase):
    def test_accepts_complete_prior_reconciliation(self):
        self.assertEqual(reconcile(*fixture(), expected_counts=(1, 1))["decision"], "PASS_PRIOR_TABLE_RECONCILIATION_SCOPED")

    def test_rejects_missing_candidate_row(self):
        v38, v39, table = fixture(); v38["completed_holds"] = []
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_identity_mismatch(self):
        v38, v39, table = fixture(); v38["completed_holds"][0]["id"] = "other"
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_display_precision_mismatch(self):
        v38, v39, table = fixture(); table["completed_holds"][0]["lower_ms"] += 0.002
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_exact_aggregate_mismatch(self):
        v38, v39, table = fixture(); table["reported_exact_precision_summaries"]["v38"]["requested_total_ms"] += 1
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_interruption_mismatch(self):
        v38, v39, table = fixture(); v39["interrupted_holds"][0]["empty_verified_ns"] += 1
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_completed_totals_with_interrupt_included(self):
        v38, v39, table = fixture(); table["interrupted_hold"]["excluded_from_completed_hold_totals"] = False
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])

    def test_rejects_keyset_mismatch(self):
        v38, v39, table = fixture(); table["completed_holds"][1]["keys"] = ["a"]
        self.assertTrue(reconcile(v38, v39, table, expected_counts=(1, 1))["errors"])


if __name__ == "__main__":
    unittest.main()
