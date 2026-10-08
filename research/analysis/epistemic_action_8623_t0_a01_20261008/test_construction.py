import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable


def invoke(script, *args, input_text=None):
    return subprocess.run(
        [PYTHON, str(ROOT / script), *map(str, args)],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def candidate_raw():
    proc = invoke("candidate.py", "--fixture", ROOT / "fixture.json")
    if proc.returncode != 0:
        raise AssertionError(f"candidate CLI must execute (exit={proc.returncode}): {proc.stderr}")
    return proc.stdout


def audit(raw_text):
    return invoke("auditor.py", "--fixture", ROOT / "fixture.json", "--oracle", ROOT / "oracle.json", input_text=raw_text)


class EpistemicActionConstructionTests(unittest.TestCase):
    def test_candidate_emits_one_row_for_every_case_and_arm(self):
        raw = json.loads(candidate_raw())
        self.assertEqual(18, len(raw["rows"]))
        self.assertEqual(18, len({(row["case_id"], row["arm"]) for row in raw["rows"]}))

    def test_independent_auditor_accepts_unmutated_candidate(self):
        result = audit(candidate_raw())
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(18, report["rows_reconstructed"])
        self.assertEqual(3, report["available_evidence_needed_successes"])
        self.assertEqual(0, report.get("no_action_evidence_needed_successes"))
        self.assertEqual(0, report["available_hard_gate_violations"])
        self.assertEqual(1, report["available_unnecessary_actions"])
        self.assertEqual(4, report["available_task_successes"])
        self.assertEqual(4, report.get("prescribed_task_successes"))
        self.assertEqual(1, report["no_action_task_successes"])

    def test_auditor_rejects_unrelated_probe_effect(self):
        raw = json.loads(candidate_raw())
        row = next(r for r in raw["rows"] if r["case_id"] == "SAFE_DISCRIMINATING_PROBE" and r["arm"] == "AVAILABLE")
        row["unrelated_side_effects"] = ["clipboard_changed"]
        result = audit(json.dumps(raw))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("UNRELATED_PROBE_EFFECT", result.stderr)

    def test_auditor_rejects_lossy_transformation(self):
        raw = json.loads(candidate_raw())
        row = next(r for r in raw["rows"] if r["case_id"] == "UNUSABLE_REPRESENTATION" and r["arm"] == "AVAILABLE")
        row["evidence_after"]["provenance"] = []
        result = audit(json.dumps(raw))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PROVENANCE_NOT_PRESERVED", result.stderr)

    def test_auditor_rejects_fabricated_provenance(self):
        raw = json.loads(candidate_raw())
        row = next(r for r in raw["rows"] if r["case_id"] == "MISSING_RETRIEVABLE" and r["arm"] == "AVAILABLE")
        row["evidence_after"]["provenance"] = ["invented-source"]
        result = audit(json.dumps(raw))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("FABRICATED_PROVENANCE", result.stderr)

    def test_auditor_rejects_unnecessary_probe_when_decision_cannot_change(self):
        raw = json.loads(candidate_raw())
        row = next(r for r in raw["rows"] if r["case_id"] == "SUFFICIENT_INITIAL_EVIDENCE" and r["arm"] == "PRESCRIBED")
        row["actions"] = ["PROBE", "COMMIT"]
        result = audit(json.dumps(raw))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("STOPPING_ORACLE_MISMATCH", result.stderr)

    def test_formal_runner_executes_once_and_refuses_to_overwrite_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp) / "formal"
            result = invoke("run_formal.py", "--output-dir", output_dir)
            self.assertEqual(0, result.returncode, result.stderr)
            run = json.loads((output_dir / "RUN.json").read_text(encoding="utf-8"))
            self.assertEqual(1, run["candidate_invocations"])
            self.assertEqual(1, run["auditor_invocations"])
            self.assertEqual(0, run["retries"])
            self.assertEqual("PASS_METHOD_SCOPED", run["formal_disposition"])
            self.assertEqual("H_PASS_SCOPED", run["hypothesis_disposition"])
            raw = (output_dir / "raw_candidate.json").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), run["candidate_stdout_sha256"])
            before = (output_dir / "RUN.json").read_bytes()
            second = invoke("run_formal.py", "--output-dir", output_dir)
            self.assertNotEqual(0, second.returncode)
            self.assertIn("OUTPUT_DIR_EXISTS", second.stderr)
            self.assertEqual(before, (output_dir / "RUN.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
