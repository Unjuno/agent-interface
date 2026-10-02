"""Construction and mutation tests; not the formal allocation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import auditor
import candidate


ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


def event(raw: dict, case_id: str, route: str, *, kind: str, status: str | None = None) -> dict:
    rows = [
        row for row in raw["events"]
        if row["case_id"] == case_id and row["route"] == route and row["kind"] == kind
    ]
    if status is not None:
        rows = [row for row in rows if row["status"] == status]
    if len(rows) != 1:
        raise AssertionError(f"expected one event, found {len(rows)}: {case_id}/{route}/{kind}/{status}")
    return rows[0]


class AdoptionCurveConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = candidate.run(FIXTURE)
        cls.audit = auditor.audit(FIXTURE, cls.raw)

    def test_exact_case_route_and_event_inventory(self) -> None:
        self.assertEqual(len(FIXTURE["cases"]), 6)
        self.assertEqual(FIXTURE["routes"], ["direct", "guarded"])
        self.assertEqual(self.audit["audit_status"], "PASS_METHOD_SCOPED", self.audit["errors"])
        self.assertEqual(self.audit["event_rows"], self.audit["reconstructed_event_rows"])

    def test_setup_dominance_changes_prepared_vs_first_use_ranking(self) -> None:
        result = self.raw["analysis"]["cases"]["setup_dominates_short_horizon"]["comparisons"]
        prepared = result["prepared_only"]["wall_ms"]
        adoption = result["adoption"]["wall_ms"]
        self.assertTrue(prepared["guarded_faster_all_comparable_n"])
        self.assertFalse(adoption["guarded_faster_all_comparable_n"])
        self.assertIsNone(prepared["crossing_after_nonbenefit_n"])
        self.assertIsNone(adoption["crossing_after_nonbenefit_n"])

    def test_failed_task_attempt_cost_is_charged_but_not_useful_work(self) -> None:
        result = self.raw["analysis"]["cases"]["learning_rank_reversal"]
        guarded = result["curves"]["guarded"]["adoption"]
        self.assertEqual(guarded["2"]["wall_ms"], 450)
        self.assertEqual(result["denominators"]["guarded"]["attempted_attempts"], 9)
        self.assertEqual(result["denominators"]["guarded"]["verified_useful_tasks"], 8)
        self.assertEqual(result["comparisons"]["prepared_only"]["wall_ms"]["crossing_after_nonbenefit_n"], 6)
        self.assertEqual(result["comparisons"]["adoption"]["wall_ms"]["crossing_after_nonbenefit_n"], 8)

    def test_failed_setup_is_charged_and_has_no_prepared_only_curve(self) -> None:
        result = self.raw["analysis"]["cases"]["setup_failure"]["curves"]["guarded"]
        self.assertEqual(result["status"], "NOT_APPLICABLE_SETUP_FAILED")
        self.assertEqual(result["adoption"]["1"]["status"], "NOT_REACHED")
        self.assertEqual(result["prepared_only"]["1"]["status"], "NOT_APPLICABLE_SETUP_FAILED")
        self.assertEqual(event(self.raw, "setup_failure", "guarded", kind="setup")["wall_ms"], 240)

    def test_app_repair_is_a_separate_cost_event(self) -> None:
        repair = event(self.raw, "app_change_repair", "guarded", kind="repair")
        self.assertEqual((repair["wall_ms"], repair["human_ms"]), (180, 100))
        curves = self.raw["analysis"]["cases"]["app_change_repair"]["curves"]["guarded"]
        self.assertEqual(curves["prepared_only"]["3"]["wall_ms"], 420)

    def test_unsupported_host_stays_unattempted_and_n4_is_not_reached(self) -> None:
        row = event(self.raw, "unsupported_host", "guarded", kind="task_opportunity", status="INELIGIBLE")
        self.assertFalse(row["attempted"])
        self.assertFalse(row["verified_useful"])
        self.assertEqual(row["wall_ms"], 0)
        self.assertEqual(
            self.raw["analysis"]["cases"]["unsupported_host"]["curves"]["guarded"]["adoption"]["4"]["status"],
            "NOT_REACHED",
        )
        for view in ("prepared_only", "adoption"):
            comparison = self.raw["analysis"]["cases"]["unsupported_host"]["comparisons"][view]["wall_ms"]
            self.assertEqual(comparison["comparable_n"], [1, 2, 3])
            self.assertEqual(comparison["first_unreached_n"], 4)
            self.assertFalse(comparison["guarded_faster_all_comparable_n"])
            self.assertTrue(comparison["guarded_faster_all_reached_n"])

    def test_auditor_rejects_dropped_setup_failure(self) -> None:
        raw = copy.deepcopy(self.raw)
        row = event(raw, "setup_failure", "guarded", kind="setup")
        raw["events"].remove(row)
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["audit_status"], "HOLD_AUDIT_INTEGRITY")
        self.assertTrue(result["errors"])

    def test_auditor_rejects_attempted_as_verified(self) -> None:
        raw = copy.deepcopy(self.raw)
        row = event(raw, "learning_rank_reversal", "guarded", kind="task_attempt", status="FAILED")
        row["status"] = "VERIFIED_SUCCESS"
        row["verified_useful"] = True
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_unsupported_host_as_success(self) -> None:
        raw = copy.deepcopy(self.raw)
        row = event(raw, "unsupported_host", "guarded", kind="task_opportunity", status="INELIGIBLE")
        row.update({"status": "VERIFIED_SUCCESS", "eligible": True, "attempted": True, "verified_useful": True, "wall_ms": 1})
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_omitted_app_repair(self) -> None:
        raw = copy.deepcopy(self.raw)
        row = event(raw, "app_change_repair", "guarded", kind="repair")
        raw["events"].remove(row)
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_dropped_setup_failure_cost(self) -> None:
        raw = copy.deepcopy(self.raw)
        event(raw, "setup_failure", "guarded", kind="setup")["wall_ms"] = 0
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["audit_status"], "HOLD_AUDIT_INTEGRITY")


if __name__ == "__main__":
    unittest.main()
