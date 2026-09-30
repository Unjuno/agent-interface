from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .audit import audit
from .model import POLICIES, SCENARIOS, classify, run_matrix, simulate


class HandoffModelTests(unittest.TestCase):
    def test_matrix_is_exact_and_complete(self):
        rows = run_matrix()
        self.assertEqual(len(rows), len(POLICIES) * len(SCENARIOS))
        self.assertEqual(len({(r["policy"], r["scenario"]) for r in rows}), len(rows))

    def test_nominal_ack_only_has_overlap_but_two_phase_does_not(self):
        scenario = next(s for s in SCENARIOS if s.name == "nominal")
        self.assertGreater(simulate("ACK_ONLY", scenario)["duplicate_owner_ticks"], 0)
        self.assertEqual(simulate("TWO_PHASE", scenario)["duplicate_owner_ticks"], 0)
        self.assertEqual(simulate("THREE_PHASE", scenario)["duplicate_owner_ticks"], 0)

    def test_human_takeover_blocks_later_automation_activation(self):
        scenario = next(s for s in SCENARIOS if s.name == "human_intervention")
        for policy in ("TWO_PHASE", "THREE_PHASE"):
            row = simulate(policy, scenario)
            self.assertTrue(all(not ({"target", "human"} <= set(t["owners"])) for t in row["trace"]))

    def test_fail_closed_never_reactivates_target(self):
        for scenario in SCENARIOS:
            row = simulate("FAIL_CLOSED_NO_OWNER", scenario)
            self.assertTrue(all("target" not in t["owners"] for t in row["trace"]))

    def test_two_phase_and_three_phase_do_not_claim_task_success(self):
        self.assertTrue(all(r["false_success_claims"] == 0 for r in run_matrix()))

    def test_independent_audit_reconciles_all_rows(self):
        rows = run_matrix()
        summary = {"rows": len(rows), "disposition": classify(rows)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.json"
            path.write_text(json.dumps({"summary": summary, "traces": rows}), encoding="utf-8")
            result = audit(path)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["status"], "PASS_HANDOFF_BOUNDARIES_SCOPED")

    def test_independent_audit_detects_mutated_metric(self):
        rows = run_matrix()
        rows[0]["authority_gap_ticks"] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.json"
            path.write_text(json.dumps({"summary": {}, "traces": rows}), encoding="utf-8")
            result = audit(path)
        self.assertTrue(any(e.startswith("metric_mismatch:") for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
