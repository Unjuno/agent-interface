import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).parent
FIXTURE = ROOT / "fixture.json"
RUNNER = ROOT / "candidate.py"
AUDIT = ROOT / "audit.py"

class DisturbanceResponseTests(unittest.TestCase):
    def run_candidate(self):
        result = subprocess.run([sys.executable, str(RUNNER)], input=FIXTURE.read_text(encoding="utf-8"), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_alias_requires_discriminating_observation_and_permitted_response(self):
        result = self.run_candidate()
        self.assertEqual(result["baseline"]["classification"], "OBSERVATION_ALIAS")
        self.assertEqual(result["extra_verifier"]["classification"], "OBSERVATION_ALIAS")
        self.assertEqual(result["added_observation"]["classification"], "AUTHORITY_GAP")
        self.assertEqual(result["added_observation"]["disturbances"][-1]["outcome"], "NO_RESPONSE")
        self.assertEqual(result["added_recovery"]["classification"], "OBSERVATION_ALIAS")
        self.assertEqual(result["added_recovery"]["disturbances"][-1]["outcome"], "COVERED")
        self.assertEqual(result["added_recovery"]["disturbances"][1]["latency_ms"], 3)
        self.assertEqual(result["combined"]["classification"], "AUTHORITY_GAP")
        self.assertEqual(result["combined"]["disturbances"][-1]["outcome"], "COVERED")
        self.assertEqual(result["forbidden_response"]["classification"], "AUTHORITY_GAP")
        self.assertEqual(result["deadline_gap"]["classification"], "DEADLINE_GAP")

    def test_all_disturbances_remain_in_raw_denominator_and_audit_rejects_omission(self):
        result = self.run_candidate()
        rows = result["baseline"]["disturbances"]
        self.assertEqual([r["disturbance_id"] for r in rows], ["focus-loss", "target-mutation", "modal-takeover", "forbidden-reset", "worker-exit"])
        good = subprocess.run([sys.executable, str(AUDIT), str(FIXTURE)], input=json.dumps(result), text=True, capture_output=True)
        self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
        result["baseline"]["disturbances"].pop()
        bad = subprocess.run([sys.executable, str(AUDIT), str(FIXTURE)], input=json.dumps(result), text=True, capture_output=True)
        self.assertNotEqual(bad.returncode, 0)

if __name__ == "__main__":
    unittest.main()
