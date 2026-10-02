import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class FixtureConstructionTests(unittest.TestCase):
    def test_required_trace_family_is_complete(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        ids = {trace["id"] for trace in fixture["traces"]}
        self.assertEqual(len(fixture["traces"]), 9)
        self.assertEqual(ids, {
            "effect_before_release", "release_before_effect", "ambiguous_save",
            "failed_verification", "collateral_effect", "cancelled_input",
            "no_pending_obligations", "independent_next_task", "stale_effect_generation",
        })

    def test_three_display_arms_are_frozen(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["displays"], [
            "A_EARLY_GENERIC", "B_TYPED_EFFECT_PENDING", "C_LATE_TERMINAL_ONLY",
        ])

    def test_stale_generation_and_accepted_without_effect_controls_exist(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        by_id = {trace["id"]: trace for trace in fixture["traces"]}
        stale = by_id["stale_effect_generation"]
        self.assertNotEqual(stale["generation"], stale["effect"]["receipt_generation"])
        ambiguous = by_id["ambiguous_save"]
        self.assertTrue(ambiguous["effect"]["accepted_input"])
        self.assertEqual(ambiguous["effect"]["state"], "UNKNOWN")

    def test_independent_tasks_have_disjoint_sources_and_obligations(self):
        trace = next(t for t in json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))["traces"] if t["id"] == "independent_next_task")
        a, b = trace["tasks"]
        self.assertNotEqual(a["source"], b["source"])
        self.assertTrue({x["id"] for x in a["obligations"]}.isdisjoint({x["id"] for x in b["obligations"]}))

    def test_candidate_and_auditor_are_independently_authored(self):
        candidate = ast.parse((ROOT / "candidate.py").read_text(encoding="utf-8"))
        auditor = ast.parse((ROOT / "auditor.py").read_text(encoding="utf-8"))
        candidate_imports = {n.module for n in ast.walk(candidate) if isinstance(n, ast.ImportFrom)}
        auditor_imports = {n.module for n in ast.walk(auditor) if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("candidate", auditor_imports)
        self.assertNotIn("auditor", candidate_imports)


if __name__ == "__main__":
    unittest.main()

