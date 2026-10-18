import json
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class DecisionValuePolicyTests(unittest.TestCase):
    def run_candidate(self, model):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "model.json"
            output_path = Path(temp_dir) / "candidate.json"
            input_path.write_text(json.dumps(model), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "candidate.py"), str(input_path), str(output_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(output_path.read_text(encoding="utf-8"))

    def test_decision_value_selects_low_information_check_that_changes_route(self):
        model = json.loads((ROOT / "fixtures" / "candidate_model.json").read_text(encoding="utf-8"))
        raw = self.run_candidate(model)
        main = next(case for case in raw["cases"] if case["case_id"] == "ig_conflict")
        policies = main["policies"]

        self.assertEqual(policies["cost_only"]["selected_check"], "nuisance")
        self.assertEqual(policies["entropy_threshold"]["selected_check"], "nuisance")
        self.assertEqual(policies["decision_value"]["selected_check"], "decision")
        self.assertEqual(policies["oracle_best_check"]["selected_check"], "decision")
        self.assertEqual(policies["decision_value"]["routes_by_outcome"]["A"], "route_a")
        self.assertEqual(policies["decision_value"]["routes_by_outcome"]["B"], "route_b")

    def test_decision_value_effect_persists_on_heldout_state_topology(self):
        model = json.loads((ROOT / "fixtures" / "candidate_model.json").read_text(encoding="utf-8"))
        raw = self.run_candidate(model)
        heldout = next(case for case in raw["cases"] if case["case_id"] == "heldout_conflict")

        self.assertEqual(heldout["policies"]["cost_only"]["selected_check"], "nuisance")
        self.assertEqual(heldout["policies"]["entropy_threshold"]["selected_check"], "nuisance")
        self.assertEqual(heldout["policies"]["decision_value"]["selected_check"], "decision")
        self.assertEqual(heldout["policies"]["decision_value"]["routes_by_outcome"]["C"], "route_c")
        self.assertEqual(heldout["policies"]["decision_value"]["routes_by_outcome"]["D"], "route_d")

    def test_decision_value_skips_redundant_or_stale_checks(self):
        model = json.loads((ROOT / "fixtures" / "candidate_model.json").read_text(encoding="utf-8"))
        raw = self.run_candidate(model)
        redundant = next(case for case in raw["cases"] if case["case_id"] == "correlated")
        stale = next(case for case in raw["cases"] if case["case_id"] == "stale")

        self.assertIsNone(redundant["policies"]["decision_value"]["selected_check"])
        self.assertEqual(stale["policies"]["decision_value"]["disposition"], "UNKNOWN")
        self.assertEqual(stale["policies"]["decision_value"]["routes_by_outcome"], {})

    def test_decision_value_yields_outside_the_declared_model_support(self):
        model = json.loads((ROOT / "fixtures" / "candidate_model.json").read_text(encoding="utf-8"))
        raw = self.run_candidate(model)
        unsupported = next(case for case in raw["cases"] if case["case_id"] == "unsupported")

        for policy in unsupported["policies"].values():
            self.assertEqual(policy["disposition"], "UNKNOWN")
            self.assertIsNone(policy["selected_check"])
            self.assertEqual(policy["routes_by_outcome"], {})

    def test_decision_value_respects_frozen_net_value_threshold(self):
        model = json.loads((ROOT / "fixtures" / "candidate_model.json").read_text(encoding="utf-8"))
        model = copy.deepcopy(model)
        model["policies"]["decision_value"]["minimum_net_value"] = 2.1
        raw = self.run_candidate(model)
        main = next(case for case in raw["cases"] if case["case_id"] == "ig_conflict")

        self.assertIsNone(main["policies"]["decision_value"]["selected_check"])
        self.assertEqual(main["policies"]["decision_value"]["routes_by_outcome"], {"__NO_CHECK__": "route_a"})

    def test_independent_scorer_reports_realized_regret_and_check_cost(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "candidate.json"
            score_path = Path(temp_dir) / "score.json"
            model_path = ROOT / "fixtures" / "candidate_model.json"
            key_path = ROOT / "fixtures" / "scoring_key.json"
            candidate = subprocess.run(
                [sys.executable, "-B", str(ROOT / "candidate.py"), str(model_path), str(raw_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(candidate.returncode, 0, candidate.stderr)
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scorer.py"), str(model_path), str(key_path), str(raw_path), str(score_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            score = json.loads(score_path.read_text(encoding="utf-8"))
            main = score["summary"]["ig_conflict"]

            self.assertEqual(main["decision_value"]["mean_regret"], 2.5)
            self.assertEqual(main["decision_value"]["mean_check_cost"], 0.5)
            self.assertEqual(main["decision_value"]["mean_regret_plus_cost"], 3.0)
            self.assertEqual(main["entropy_threshold"]["mean_regret"], 5.0)
            self.assertEqual(main["entropy_threshold"]["mean_regret_plus_cost"], 5.1)
            heldout = score["summary"]["heldout_conflict"]
            self.assertEqual(heldout["decision_value"]["mean_regret"], 2.5)
            self.assertEqual(heldout["entropy_threshold"]["mean_regret"], 5.0)

    def test_independent_auditor_rejects_changed_policy_choice(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "candidate.json"
            score_path = Path(temp_dir) / "score.json"
            audit_path = Path(temp_dir) / "audit.json"
            model_path = ROOT / "fixtures" / "candidate_model.json"
            key_path = ROOT / "fixtures" / "scoring_key.json"
            candidate = subprocess.run(
                [sys.executable, "-B", str(ROOT / "candidate.py"), str(model_path), str(raw_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(candidate.returncode, 0, candidate.stderr)
            score = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scorer.py"), str(model_path), str(key_path), str(raw_path), str(score_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(score.returncode, 0, score.stderr)
            audit = subprocess.run(
                [sys.executable, "-B", str(ROOT / "auditor.py"), str(model_path), str(key_path), str(raw_path), str(score_path), str(audit_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            valid = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(valid["disposition"], "PASS_METHOD_SCOPED")
            self.assertEqual(valid["errors"], [])

            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            conflict = next(case for case in raw["cases"] if case["case_id"] == "ig_conflict")
            conflict["policies"]["decision_value"]["selected_check"] = "nuisance"
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            tampered = subprocess.run(
                [sys.executable, "-B", str(ROOT / "auditor.py"), str(model_path), str(key_path), str(raw_path), str(score_path), str(audit_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(tampered.returncode, 0, tampered.stderr)
            rejected = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertNotEqual(rejected["disposition"], "PASS_METHOD_SCOPED")
            self.assertTrue(rejected["errors"])


if __name__ == "__main__":
    unittest.main()
