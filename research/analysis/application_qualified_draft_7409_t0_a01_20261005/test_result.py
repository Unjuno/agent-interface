"""Verify retained Issue #7409 T0 evidence without rerunning candidate/auditor."""
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "frozen"
RESULTS = ROOT / "results" / "a01"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RetainedResultTests(unittest.TestCase):
    def test_frozen_source_hashes(self):
        freeze = read_json(FROZEN / "FREEZE.json")
        for name, expected in freeze["source_sha256"].items():
            actual = hashlib.sha256((FROZEN / name).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, name)

    def test_run_output_hashes_and_single_invocations(self):
        metadata = read_json(RESULTS / "run_metadata.json")
        self.assertEqual({"preflight": 1, "candidate": 1, "auditor_after_candidate_exit_0": 1, "retries": 0}, metadata["invocation_counts"])
        self.assertEqual(0, metadata["candidate_exit_code"])
        self.assertEqual(0, metadata["auditor_exit_code"])
        self.assertEqual("0\n", (RESULTS / "candidate.exit_code.txt").read_text())
        self.assertEqual("0\n", (RESULTS / "auditor.exit_code.txt").read_text())
        for name, expected in metadata["outputs"].items():
            actual = hashlib.sha256((RESULTS / name).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, name)

    def test_audit_gate_and_mutations(self):
        audit = read_json(RESULTS / "audit.json")
        self.assertEqual("METHOD_PASS_SCOPED", audit["disposition"])
        self.assertEqual(6, audit["reconstructed_rows"])
        self.assertEqual([], audit["errors"])
        self.assertEqual(6, audit["mutation_controls_rejected"])
        self.assertEqual(6, audit["mutation_controls_total"])
        self.assertTrue(all(audit["mutations"].values()))

    def test_staged_outcomes_preserve_conflict_and_scope_gates(self):
        raw = read_json(RESULTS / "candidate.raw.json")
        rows = {row["case_id"]: row for row in raw["rows"]}
        self.assertEqual(6, len(rows))
        self.assertEqual("human", rows["C1-disjoint"]["staged"]["final"]["owner"])
        self.assertEqual("agent summary", rows["C1-disjoint"]["staged"]["final"]["summary"])
        self.assertEqual("r3", rows["C4-revision-changed-disjoint"]["staged"]["final_revision"])
        self.assertTrue(rows["C4-revision-changed-disjoint"]["staged"]["revision_checked"])
        for case_id in ("C2-same-field", "C3-hidden-dependency"):
            self.assertEqual("CONFLICT_HOLD", rows[case_id]["staged"]["status"])
            self.assertFalse(rows[case_id]["staged"]["promoted"])
        for case_id in ("C5-shared-backend-autosave", "C6-external-side-effect"):
            staged = rows[case_id]["staged"]
            self.assertEqual("REFUSED_ELIGIBILITY", staged["status"])
            self.assertFalse(staged["draft_created"])
            self.assertEqual([], staged["external_effects"])


if __name__ == "__main__":
    unittest.main()
