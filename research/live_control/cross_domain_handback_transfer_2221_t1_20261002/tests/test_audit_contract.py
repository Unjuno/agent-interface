"""The independent auditor must reject plausible cross-domain evidence laundering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
CANDIDATE = PACKAGE / "candidate.py"
AUDITOR = PACKAGE / "audit.py"


def produce_and_audit(mutation=None):
    temp = tempfile.TemporaryDirectory(prefix="handback-audit-")
    root = Path(temp.name)
    candidate_path = root / "candidate.json"
    audit_path = root / "audit.json"
    candidate = subprocess.run(
        [sys.executable, str(CANDIDATE), "--repo-root", str(REPO),
         "--output", str(candidate_path)], capture_output=True, text=True)
    if candidate.returncode != 0:
        temp.cleanup()
        raise AssertionError(candidate.stderr)
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    if mutation:
        mutation(payload)
    candidate_path.write_text(json.dumps(payload), encoding="utf-8")
    audit = subprocess.run(
        [sys.executable, str(AUDITOR), "--repo-root", str(REPO),
         "--candidate", str(candidate_path), "--output", str(audit_path)],
        capture_output=True, text=True)
    result = (json.loads(audit_path.read_text(encoding="utf-8"))
              if audit_path.exists() else None)
    temp.cleanup()
    return audit, result


class AuditContractTests(unittest.TestCase):
    def test_independent_auditor_accepts_source_bound_scoped_projection(self):
        run, result = produce_and_audit()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED")
        self.assertEqual(result["checks_passed"], 10)

    def test_rejects_viewport_change_promoted_to_task_effect(self):
        def promote(payload):
            row = next(x for x in payload["records"]
                       if x["case_id"] == "doom-v39-first-plan-frames")
            row["evidence_type"] = "TASK_EFFECT"
            row["task_effect"] = "USEFUL_CURRENT_EFFECT"

        run, result = produce_and_audit(promote)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("doom_observed_change_stays_unresolved", result["failed_checks"])

    def test_rejects_cross_clock_latency_join(self):
        def join_clocks(payload):
            row = next(x for x in payload["records"]
                       if x["case_id"] == "browser-direct-task6-save")
            row["clock_join"] = "JOINED"

        run, result = produce_and_audit(join_clocks)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("no_authority_or_cross_source_clock_join", result["failed_checks"])

    def test_rejects_release_relabelled_as_task_effect(self):
        def relabel(payload):
            row = next(x for x in payload["records"]
                       if x["case_id"] == "doom-v39-typed-revocation-release")
            row["evidence_type"] = "TASK_EFFECT"
            row["task_effect"] = "DONE"

        run, result = produce_and_audit(relabel)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("release_not_task_effect", result["failed_checks"])

    def test_rejects_visual_acknowledgement_invention(self):
        def invent_ack(payload):
            row = next(x for x in payload["records"]
                       if x["case_id"] == "browser-direct-task6-save")
            row["visual_acknowledgement"] = "CONFIRMED"

        run, result = produce_and_audit(invent_ack)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("visual_ack_remains_unknown", result["failed_checks"])

    def test_rejects_authority_expansion(self):
        def grant(payload):
            payload["records"][0]["semantic_authority"] = True

        run, result = produce_and_audit(grant)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("no_authority_or_cross_source_clock_join", result["failed_checks"])

    def test_rejects_unbound_source_provenance(self):
        def forge_source(payload):
            row = next(x for x in payload["records"]
                       if x["case_id"] == "browser-direct-task6-save")
            row["source"]["sha256"] = "0" * 64

        run, result = produce_and_audit(forge_source)
        self.assertNotEqual(run.returncode, 0)
        self.assertIsNotNone(result)
        self.assertIn("source_lineage_pinned", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
