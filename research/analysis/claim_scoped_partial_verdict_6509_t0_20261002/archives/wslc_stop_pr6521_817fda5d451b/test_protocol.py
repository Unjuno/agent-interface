"""Host-only construction tests; not a formal WSLc result."""
import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


FIXTURE = json.loads(Path(__file__).with_name("fixture.json").read_text(encoding="utf-8"))


class ClaimLadderTests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.build_raw(FIXTURE)

    def test_denominator_and_expected_claim_ladder(self):
        self.assertEqual(len(self.raw["rows"]), 36)
        report = auditor.audit(self.raw)
        self.assertEqual(report["status"], "METHOD_PASS_SCOPED", report["errors"])

    def test_every_partial_claim_ladder_row_is_non_authoritative(self):
        for row in self.raw["rows"]:
            if row["policy"] == "CLAIM_LADDER" and row["result"]["disposition"] == "PARTIAL_UNKNOWN":
                self.assertFalse(row["result"]["authority"], row["trace_id"])

    def test_scalar_negative_control_is_caught(self):
        rows = [r for r in self.raw["rows"] if r["policy"] == "UNSAFE_SCALAR_PROGRESS"]
        self.assertTrue(any(r["result"]["disposition"] == "ALLOW" and
                            r["trace_id"] in ("false-scalar-positive", "dropped-mandatory") for r in rows))

    def test_uncommitted_crash_receipt_is_not_counted(self):
        row = next(r for r in self.raw["rows"] if r["trace_id"] == "crash-receipt-before-commit" and
                   r["policy"] == "CLAIM_LADDER")
        self.assertEqual(row["result"]["completed"], [])

    def test_stale_and_external_change_never_allow(self):
        for trace_id in ("stale-generation", "external-state-change"):
            row = next(r for r in self.raw["rows"] if r["trace_id"] == trace_id and
                       r["policy"] == "CLAIM_LADDER")
            self.assertEqual(row["result"]["disposition"], "PARTIAL_UNKNOWN")

    def test_corrupt_disposition_fails_independent_audit(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["trace_id"] == "timeout-after-prefix" and
                   r["policy"] == "CLAIM_LADDER")
        row["result"]["disposition"] = "COMPLETE_ALLOW"
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")

    def test_partial_authority_mutation_fails(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["trace_id"] == "timeout-after-prefix" and
                   r["policy"] == "CLAIM_LADDER")
        row["result"]["authority"] = True
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")

    def test_wrong_denominator_fails(self):
        mutated = copy.deepcopy(self.raw)
        mutated["rows"].pop()
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")

    def test_frozen_trace_substitution_fails(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["trace_id"] == "timeout-after-prefix")
        row["input"]["events"].clear()
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")

    def test_forged_completed_check_list_fails(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["trace_id"] == "timeout-after-prefix" and
                   r["policy"] == "CLAIM_LADDER")
        row["result"]["completed"].append("effect")
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")

    def test_unbound_early_negative_is_not_a_counterexample(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["trace_id"] == "complete-negative" and
                   r["policy"] == "CLAIM_LADDER")
        row["input"]["events"][2][3] = False
        self.assertEqual(auditor.audit(mutated)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
