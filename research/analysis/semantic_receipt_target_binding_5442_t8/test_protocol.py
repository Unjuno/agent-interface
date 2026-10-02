"""Host-only construction controls, not formal candidate/auditor invocations."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CANDIDATE = load("candidate_t8", "candidate.py")
AUDITOR = load("auditor_t8", "audit.py")


class TargetBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (HERE / "scenarios.json").read_bytes()
        cls.raw = CANDIDATE.run(cls.source)

    def test_frozen_four_case_decision_and_commit_table(self):
        self.assertEqual(
            [(r["scenario_id"], r["intermediate_status"], r["semantic_status"], r["commit_admitted"]) for r in self.raw["rows"]],
            [("valid_effect", "SUCCESS", "SEMANTICALLY_CONFIRMED", True),
             ("wrong_target", "SUCCESS", "UNKNOWN", False),
             ("stale_pre_state", "SUCCESS", "UNKNOWN", False),
             ("noop", "SUCCESS", "UNKNOWN", False)],
        )

    def test_actual_nested_intent_target_corruption_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"][0]["receipt"]["intent"]["target_id"] = "doc:B"
        self.assertTrue(AUDITOR.assess(changed, self.source))

    def test_actual_endpoint_target_corruption_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"][0]["receipt"]["endpoint"]["target_id"] = "doc:B"
        self.assertTrue(AUDITOR.assess(changed, self.source))

    def test_wrong_target_cannot_admit_irreversible_commit(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"][1]["commit_admitted"] = True
        self.assertTrue(AUDITOR.assess(changed, self.source))

    def test_scenario_source_target_mutation_is_rejected(self):
        fixture = json.loads(self.source)
        fixture["scenarios"][0]["intent"]["target_id"] = "doc:B"
        altered = json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()
        self.assertTrue(AUDITOR.assess(self.raw, altered))

    def test_audit_self_controls_cover_actual_target_and_structure(self):
        errors = AUDITOR.assess(self.raw, self.source)
        self.assertEqual(errors, [])
        script = (HERE / "audit.py").read_text()
        self.assertIn('"actual_intent_target"', script)
        self.assertIn('"scenario_source_intent_target"', script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
