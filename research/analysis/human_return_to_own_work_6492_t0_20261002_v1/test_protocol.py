import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ReturnToWorkProtocolTests(unittest.TestCase):
    def run_candidate_and_auditor(self, tmp):
        raw = Path(tmp) / "candidate.json"
        audit = Path(tmp) / "audit.json"
        freeze = Path(tmp) / "freeze.json"
        hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                  for name in ("fixture.json", "oracle.json", "candidate.py", "audit.py")}
        freeze.write_text(json.dumps({"sha256": hashes}), encoding="utf-8")
        candidate = subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--fixture", str(ROOT / "fixture.json"), "--output", str(raw)], capture_output=True, text=True)
        self.assertEqual(candidate.returncode, 0, candidate.stdout + candidate.stderr)
        auditor = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--fixture", str(ROOT / "fixture.json"), "--oracle", str(ROOT / "oracle.json"), "--raw", str(raw), "--freeze", str(freeze), "--output", str(audit)], capture_output=True, text=True)
        self.assertEqual(auditor.returncode, 0, auditor.stdout + auditor.stderr)
        return json.loads(raw.read_text(encoding="utf-8")), json.loads(audit.read_text(encoding="utf-8"))

    def test_matched_arms_bound_source_and_keep_cue_non_authoritative(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, report = self.run_candidate_and_auditor(tmp)
        self.assertEqual(report["status"], "METHOD_PASS_SCOPED", report["errors"])
        self.assertEqual(report["cases_per_arm"], 6)
        self.assertEqual(report["rows"], 18)
        self.assertTrue(all(report["corruptions_rejected"].values()))
        rows = {r["case_id"] + "/" + r["arm"]: r for r in raw["rows"]}
        self.assertEqual(rows["case01/optional_cue"]["cue"]["text"], "finish the second row")
        self.assertEqual(rows["case02/optional_cue"]["cue"]["status"], "stale_withheld")
        self.assertTrue(rows["case02/optional_cue"]["state_change_warning"])
        self.assertEqual(rows["case04/optional_cue"]["delay_ms"], 0)
        self.assertNotIn("correct_return_action", json.dumps(raw))
        self.assertNotIn("screenshot_bytes", json.dumps(raw))


if __name__ == "__main__":
    unittest.main(verbosity=2)
