from __future__ import annotations

import json
import unittest
from pathlib import Path

from candidate import build_ledger, classify_interval
from audit import audit, validate_records

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


class TypedMarginContractTests(unittest.TestCase):
    def test_eight_opportunities_and_four_typed_groups(self) -> None:
        rows = build_ledger(PLAN)
        self.assertEqual(8, sum(row["record_type"] == "opportunity" for row in rows))
        self.assertEqual(4, sum(row["record_type"] == "typed_summary" for row in rows))
        self.assertEqual([], validate_records(PLAN, rows))

    def test_exact_zero_is_not_crossing_and_negative_interval_is(self) -> None:
        self.assertEqual("NOT_CROSSED", classify_interval({"status": "MEASURED", "lower": 0, "upper": 0, "threshold": 0}))
        self.assertEqual("CROSSED", classify_interval({"status": "MEASURED", "lower": -3, "upper": -1, "threshold": 0}))

    def test_straddling_interval_is_uncertain(self) -> None:
        self.assertEqual("UNCERTAIN_INTERVAL_STRADDLES_THRESHOLD", classify_interval({"status": "MEASURED", "lower": -1, "upper": 1, "threshold": 0}))

    def test_safe_stop_and_blocked_proposal_have_no_actuation_margin(self) -> None:
        rows = {row.get("opportunity_id"): row for row in build_ledger(PLAN) if row["record_type"] == "opportunity"}
        self.assertEqual("NO_ACTUATION_MARGIN", rows["op-safe-stop"]["actuation_margin_status"])
        self.assertEqual("NO_ACTUATION_MARGIN", rows["op-blocked-negative-proposal"]["actuation_margin_status"])
        self.assertEqual("CROSSED", rows["op-blocked-negative-proposal"]["margin"]["classification"])
        self.assertEqual("proposal_admission", rows["op-blocked-negative-proposal"]["margin"]["purpose"])

    def test_missing_timestamp_is_unknown_not_zero(self) -> None:
        rows = {row.get("opportunity_id"): row for row in build_ledger(PLAN) if row["record_type"] == "opportunity"}
        self.assertEqual("UNKNOWN", rows["op-missing-timestamp"]["margin"]["classification"])
        self.assertIsNone(rows["op-missing-timestamp"]["margin"]["lower"])

    def test_independent_auditor_rejects_all_ten_mutations(self) -> None:
        rows = build_ledger(PLAN)
        raw = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows).encode()
        import hashlib
        execution = {
            "allocation": PLAN["allocation"],
            "frozen_main": PLAN["frozen_main"],
            "candidate_exit": 0,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "image_ref": "python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8f910824d4e93bdce61e212c7e87168123ea3073b41a1a",
            "image_id": "sha256:febd0be41adb897a0ab8f1f1c693d8912669ea60c4940e076e9946b60e210ef0",
            "platform": "linux/amd64",
        }
        report = audit(PLAN, raw, execution)
        self.assertEqual("PASS_TYPED_MARGIN_CONTRACT_SCOPED", report["status"])
        self.assertEqual(10, report["corruption_controls_rejected"])
        self.assertTrue(all(item["rejected"] for item in report["corruption_controls"]))


if __name__ == "__main__":
    unittest.main()
