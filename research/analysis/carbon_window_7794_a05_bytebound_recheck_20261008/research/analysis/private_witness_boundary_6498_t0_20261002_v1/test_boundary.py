import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PrivateWitnessBoundaryTests(unittest.TestCase):
    def test_statement_truth_is_not_promoted_to_capture_or_effect_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, report, freeze = (Path(tmp) / name for name in ("raw.json", "report.json", "freeze.json"))
            names = ("fixture.json", "oracle.json", "candidate.py", "audit.py")
            freeze.write_text(json.dumps({"sha256": {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}}), encoding="utf-8")
            candidate = subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--fixture", str(ROOT / "fixture.json"), "--output", str(raw)], capture_output=True, text=True)
            self.assertEqual(candidate.returncode, 0, candidate.stdout + candidate.stderr)
            audit = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--fixture", str(ROOT / "fixture.json"), "--oracle", str(ROOT / "oracle.json"), "--raw", str(raw), "--freeze", str(freeze), "--output", str(report)], capture_output=True, text=True)
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            candidate_rows = json.loads(raw.read_text(encoding="utf-8"))["rows"]
            result = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED", result["errors"])
        self.assertEqual(len(candidate_rows), 8)
        self.assertTrue(all(result["corruptions_rejected"].values()))
        adjudicated = {r["case_id"]: r for r in result["adjudications"]}
        self.assertTrue(adjudicated["case01"]["computation_statement_true"])
        self.assertEqual(adjudicated["case01"]["boundary"], "COMPUTATION_TRUE_PREDICATE_ONLY")
        self.assertEqual(adjudicated["case01"]["task_effect_claim"], "NOT_ESTABLISHED_BY_T0")
        self.assertEqual(adjudicated["case03"]["boundary"], "COVERAGE_UNPROVEN")
        self.assertEqual(adjudicated["case04"]["boundary"], "PREOUTCOME_COMMITMENT_UNPROVEN")
        self.assertEqual(adjudicated["case05"]["boundary"], "FRESHNESS_UNPROVEN")
        self.assertEqual(adjudicated["case07"]["boundary"], "ORIGIN_UNPROVEN")
        self.assertEqual(adjudicated["case08"]["boundary"], "PREDICATE_INSUFFICIENT")
        self.assertFalse(any(r.get("whole_task_success") for r in candidate_rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
