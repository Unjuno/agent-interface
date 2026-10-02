import json
import unittest
from pathlib import Path

import auditor
import candidate

FIXTURE = json.loads(Path("fixture.json").read_text(encoding="utf-8"))
ORACLE = json.loads(Path("oracle.json").read_text(encoding="utf-8"))


class ProtocolTests(unittest.TestCase):
    def test_denominator_and_discriminating_cases(self):
        self.assertEqual(len(FIXTURE["cases"]), 10)
        self.assertEqual(len(FIXTURE["policies"]), 5)
        self.assertEqual(len(candidate.run(FIXTURE)["rows"]), 50)

    def test_independent_oracle_accepts_only_exact_origin(self):
        raw = candidate.run(FIXTURE)
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["errors"], [])

    def test_origin_fence_blocks_rebound_and_retired_lineage(self):
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(FIXTURE)["rows"]}
        for case_id in ("old_event_original_instance", "accepted_handoff_old_event", "restart_retirement_receipt_present"):
            self.assertNotEqual(rows[(case_id, "ORIGIN_GENERATION_RETIREMENT_FENCE")]["decision"], "ADMIT")
        self.assertEqual(rows[("old_event_rebound_missing_origin", "ORIGIN_GENERATION_RETIREMENT_FENCE")]["decision"], "UNKNOWN")

    def test_fresh_generation_remains_live(self):
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(FIXTURE)["rows"]}
        self.assertEqual(rows[("fresh_reused_cue_generation_B", "ORIGIN_GENERATION_RETIREMENT_FENCE")]["decision"], "ADMIT")
        self.assertEqual(rows[("unaccepted_handoff_A_still_active", "ORIGIN_GENERATION_RETIREMENT_FENCE")]["decision"], "ADMIT")

    def test_missing_origin_is_unknown_and_obligations_survive(self):
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(FIXTURE)["rows"]}
        for case_id in ("old_event_rebound_missing_origin", "restart_origin_and_receipt_missing"):
            row = rows[(case_id, "ORIGIN_GENERATION_RETIREMENT_FENCE")]
            self.assertEqual(row["decision"], "UNKNOWN")
            self.assertEqual(row["obligation_status"], FIXTURE["cases"][[c["id"] for c in FIXTURE["cases"]].index(case_id)]["obligation"])
            self.assertFalse(row["effect_resolved"])
            self.assertFalse(row["release_resolved"])

    def test_standard_instance_id_baseline_handles_correctly_bound_old_event(self):
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(FIXTURE)["rows"]}
        self.assertEqual(rows[("old_event_original_instance", "DURABLE_INSTANCE_EVENT_ID")]["decision"], "REFUSE")
        self.assertEqual(rows[("fresh_reused_cue_generation_B", "DURABLE_INSTANCE_EVENT_ID")]["decision"], "ADMIT")

    def test_original_old_event_has_preserved_origin_and_rebind_case_does_not(self):
        cases = {case["id"]: case for case in FIXTURE["cases"]}
        self.assertEqual(cases["old_event_original_instance"]["event"]["origin"]["instance"], "wait-A")
        self.assertIsNone(cases["old_event_rebound_missing_origin"]["event"]["origin"])

    def test_oracle_mutation_exposes_lineage_misattribution(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "fresh_reused_cue_generation_B" and r["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE")
        row["response_lineage"] = "wait-A"
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertTrue(any(e["kind"] == "origin_fence_misattributed_fresh_response" for e in result["errors"]))

    def test_deleted_row_rejected(self):
        raw = candidate.run(FIXTURE)
        raw["rows"].pop()
        self.assertTrue(any(e["kind"] == "denominator_mismatch" for e in auditor.audit(FIXTURE, ORACLE, raw)["errors"]))

    def test_duplicate_row_rejected(self):
        raw = candidate.run(FIXTURE)
        raw["rows"].append(raw["rows"][0].copy())
        self.assertTrue(any(e["kind"] == "duplicate_row" for e in auditor.audit(FIXTURE, ORACLE, raw)["errors"]))

    def test_origin_fence_bypass_rejected(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "old_event_rebound_missing_origin" and r["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE")
        row.update(decision="ADMIT", response_lineage="wait-B")
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertEqual(result["status"], "FAIL_OR_HOLD")

    def test_false_obligation_resolution_rejected(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "restart_origin_and_receipt_missing" and r["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE")
        row["release_resolved"] = True
        self.assertTrue(any(e["kind"] == "obligation_laundering" for e in auditor.audit(FIXTURE, ORACLE, raw)["errors"]))


if __name__ == "__main__":
    unittest.main()
