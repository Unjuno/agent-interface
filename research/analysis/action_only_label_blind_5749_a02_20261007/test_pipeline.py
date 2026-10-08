"""Construction tests for scorer-isolated action-only adaptation."""

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / script), *map(str, args)],
                          capture_output=True, text=True, check=False)


class LabelBlindPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = {
            "schema": "5749-a02-policy-input-v1",
            "allocation": "5749-ACTION-ONLY-LABEL-BLIND-A02-20261007",
            "choices": ["A", "B"], "default": "A",
            "policies": ["static_default", "clarify_each_turn", "action_only_adaptive"],
            "episodes": [{"id": "stable_B", "turns": [
                {"scope": "file-format", "consent": True, "observed_action": "B", "answer": None, "query_allowed": True},
                {"scope": "file-format", "consent": True, "observed_action": "B", "answer": None, "query_allowed": True},
                {"scope": "file-format", "consent": True, "observed_action": "B", "answer": "B", "query_allowed": True},
            ]}],
        }
        self.key = {"schema": "5749-a02-scoring-key-v1", "targets": [
            {"episode_id": "stable_B", "tick": 0, "target": "B"},
            {"episode_id": "stable_B", "tick": 1, "target": "B"},
            {"episode_id": "stable_B", "tick": 2, "target": "B"},
        ]}
        self.policy_path = self.root / "policy.json"
        self.key_path = self.root / "key.json"
        self.raw_path = self.root / "raw.json"
        self.score_path = self.root / "score.json"
        self.policy_path.write_text(json.dumps(self.policy))
        self.key_path.write_text(json.dumps(self.key))
        self.freeze_path = self.root / "freeze.json"
        self.freeze_path.write_text(json.dumps({
            "policy_input_sha256": hashlib.sha256(self.policy_path.read_bytes()).hexdigest(),
            "scoring_key_sha256": hashlib.sha256(self.key_path.read_bytes()).hexdigest(),
            "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                            for name in ("candidate.py", "scorer.py", "audit_core.py", "auditor.py")},
        }))

    def candidate(self):
        return run("candidate.py", "--freeze", self.freeze_path, self.policy_path, self.raw_path)

    def tearDown(self):
        self.temp.cleanup()

    def test_candidate_emits_policy_rows_without_scorer_labels_or_authority(self):
        result = self.candidate()
        self.assertEqual(result.returncode, 0, result.stderr)
        raw = json.loads(self.raw_path.read_text())
        self.assertEqual(raw["schema"], "5749-a02-policy-output-v1")
        self.assertEqual(len(raw["rows"]), 9)
        self.assertTrue(all("target" not in row and "wrong_proposal" not in row for row in raw["rows"]))
        self.assertTrue(all(row["authority_granted"] is False for row in raw["rows"]))
        adaptive = [r["proposal"] for r in raw["rows"] if r["policy"] == "action_only_adaptive"]
        self.assertEqual(adaptive, ["A", None, "B"])

    def test_candidate_rejects_hidden_target_field_in_policy_input(self):
        self.policy["episodes"][0]["turns"][0]["target"] = "A"
        self.policy_path.write_text(json.dumps(self.policy))
        result = self.candidate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected_policy_field", result.stderr)

    def test_separate_scorer_reads_key_only_after_candidate_output_exists(self):
        self.assertEqual(self.candidate().returncode, 0)
        result = run("scorer.py", self.raw_path, self.key_path, self.score_path, "--freeze", self.freeze_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        score = json.loads(self.score_path.read_text())
        self.assertEqual(score["summary"]["action_only_adaptive"]["proposals"], 2)
        self.assertEqual(score["summary"]["action_only_adaptive"]["wrong"], 1)
        self.assertNotIn("target", json.loads(self.raw_path.read_text())["rows"][0])

    def test_independent_auditor_rejects_raw_and_score_mutations(self):
        self.assertEqual(self.candidate().returncode, 0)
        self.assertEqual(run("scorer.py", self.raw_path, self.key_path, self.score_path,
                             "--freeze", self.freeze_path).returncode, 0)
        result = run("auditor.py", self.policy_path, self.key_path, self.raw_path, self.score_path,
                     "--freeze", self.freeze_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        audit = json.loads(result.stdout)
        self.assertEqual(audit["disposition"], "PASS_LABEL_BLIND_METHOD_SCOPED")
        self.assertGreaterEqual(audit["raw_mutations_rejected"], 4)

    def test_fresh_frozen_fixture_runs_candidate_then_scorer_then_auditor(self):
        fixture_dir = ROOT / "fixtures"
        policy_path = fixture_dir / "policy_input.json"
        key_path = fixture_dir / "scoring_key.json"
        raw_path, score_path = self.root / "formal.raw.json", self.root / "formal.score.json"
        freeze_path = self.root / "formal.freeze.json"
        policy_bytes, key_bytes = policy_path.read_bytes(), key_path.read_bytes()
        freeze_path.write_text(json.dumps({
            "policy_input_sha256": hashlib.sha256(policy_bytes).hexdigest(),
            "scoring_key_sha256": hashlib.sha256(key_bytes).hexdigest(),
            "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                            for name in ("candidate.py", "scorer.py", "audit_core.py", "auditor.py")},
        }))
        result = run("candidate.py", "--freeze", freeze_path, policy_path, raw_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(run("scorer.py", raw_path, key_path, score_path, "--freeze", freeze_path).returncode, 0)
        result = run("auditor.py", policy_path, key_path, raw_path, score_path, "--freeze", freeze_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        audit = json.loads(result.stdout)
        self.assertEqual(audit["rows"], 63)
        self.assertEqual(audit["disposition"], "PASS_LABEL_BLIND_METHOD_SCOPED")
        self.assertTrue(all("target" not in row and "wrong_proposal" not in row
                            for row in json.loads(raw_path.read_text())["rows"]))
        raw = json.loads(raw_path.read_text())
        adaptive = {(r["episode_id"], r["tick"]): r["proposal"] for r in raw["rows"]
                    if r["policy"] == "action_only_adaptive"}
        self.assertEqual([adaptive[("stable_B", i)] for i in range(3)], ["A", None, "B"])
        self.assertEqual([adaptive[("scope_change", i)] for i in range(4)], ["A", None, "A", None])
        self.assertEqual([adaptive[("consent_revoked", i)] for i in range(4)], ["A", None, "A", "A"])
        self.assertEqual([adaptive[("preference_change", i)] for i in range(4)], ["A", None, "B", None])


if __name__ == "__main__":
    unittest.main()
