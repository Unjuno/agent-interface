import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class GateExperimentTests(unittest.TestCase):
    def test_candidate_and_independent_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "candidate.jsonl"
            audit = Path(tmp) / "audit.json"
            subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(raw)], check=True)
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--input", str(raw), "--fixtures", str(ROOT / "fixtures.json"), "--output", str(audit)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(audit.read_text())
            self.assertEqual(payload["status"], "PASS_SURROGATE_GATE_SCOPED")
            self.assertEqual(payload["attempt_count"], 24)
            self.assertEqual(payload["world_count"], 5)
            for result in payload["results"].values():
                self.assertTrue(result["naive_intermediate_only_rule_promotes"])
            self.assertIn("PREDICTIVE_VALIDITY_UNESTABLISHED", payload["results"]["concordant"]["disposition"])
            for world in ("unrelated", "common_cause", "paradox", "incomplete"):
                self.assertFalse(payload["results"][world]["disposition"].startswith("DIRECTION_CONCORDANT"))

    def test_auditor_rejects_dropped_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "candidate.jsonl"
            audit = Path(tmp) / "audit.json"
            subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(raw)], check=True)
            lines = raw.read_text().splitlines()
            del lines[0]
            raw.write_text("\n".join(lines) + "\n")
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--input", str(raw), "--fixtures", str(ROOT / "fixtures.json"), "--output", str(audit)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL_AUDIT", result.stdout)

    def test_auditor_rejects_changed_stratum(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "candidate.jsonl"
            audit = Path(tmp) / "audit.json"
            subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(raw)], check=True)
            lines = raw.read_text().splitlines()
            changed = 0
            for index, line in enumerate(lines):
                item = json.loads(line)
                row = item.get("record", {})
                if row.get("world") == "concordant" and row.get("stratum") == "route_a":
                    row["stratum"] = "tampered"
                    lines[index] = json.dumps(item, sort_keys=True)
                    changed += 1
            self.assertEqual(changed, 2)
            raw.write_text("\n".join(lines) + "\n")
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--input", str(raw), "--fixtures", str(ROOT / "fixtures.json"), "--output", str(audit)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL_AUDIT", result.stdout)


if __name__ == "__main__":
    unittest.main()
