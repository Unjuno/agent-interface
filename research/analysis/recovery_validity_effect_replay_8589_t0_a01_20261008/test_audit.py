import copy
import json
from pathlib import Path
import unittest

from auditor import audit_payload
from auditor import mutation_suite
from candidate import plan_recovery
from auditor import audit_formal
from run_candidate import evaluate


CASE = {
    "case_id": "unchanged_input",
    "provenance_complete": True,
    "current_versions": {"cfg": 1},
    "nodes": [{"id": "derive", "kind": "compute", "deps": [], "reads": {"cfg": 1}}],
}
TRUTH = {
    "cases": {
        "unchanged_input": {
            "provenance_complete": True,
            "current_versions": {"cfg": 1},
            "nodes": [{"id": "derive", "kind": "compute", "deps": [], "reads": {"cfg": 1}}],
        }
    }
}
PLAN = {
    "disposition": "PASS_PLAN",
    "recompute": {
        "FULL_RESTART": ["derive"],
        "EARLIEST_CONFLICT_SUFFIX": [],
        "SELECTIVE_VALIDITY_RECOVERY": [],
    },
    "reused": {
        "FULL_RESTART": [],
        "EARLIEST_CONFLICT_SUFFIX": ["derive"],
        "SELECTIVE_VALIDITY_RECOVERY": ["derive"],
    },
    "dispatch_effects": [],
    "reconcile_effects": [],
    "preserved_effects": [],
    "historical_verifications": [],
    "effect_nodes": [],
}
RAW = {"results": [{"case_id": "unchanged_input", "plan": PLAN}]}


class IndependentAuditTests(unittest.TestCase):
    def test_frozen_corpus_passes_independent_policy_and_effect_audit(self):
        root = Path(__file__).parent
        with (root / "input.json").open(encoding="utf-8") as stream:
            inputs = json.load(stream)
        with (root / "truth.json").open(encoding="utf-8") as stream:
            truth = json.load(stream)

        result = audit_formal(inputs, truth, evaluate(inputs))

        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["reconstructed_cases"], 8)
        self.assertEqual(result["mutations_rejected"], 5)
        self.assertGreaterEqual(result["metrics"]["strict_selective_advantage_cases"], 1)

    def test_reconstructs_a_valid_raw_plan(self):
        result = audit_payload({"cases": [CASE]}, TRUTH, RAW)

        self.assertEqual(result["errors"], [])
        self.assertEqual(result["reconstructed_cases"], 1)

    def test_rejects_reuse_of_a_stale_generation(self):
        mutated = copy.deepcopy(RAW)
        mutated["results"][0]["plan"]["reused"]["SELECTIVE_VALIDITY_RECOVERY"].append("stale")

        result = audit_payload({"cases": [CASE]}, TRUTH, mutated)

        self.assertNotEqual(result["errors"], [])

    def test_rejects_a_candidate_graph_with_a_missing_dependency(self):
        changed = copy.deepcopy(CASE)
        changed["nodes"][0]["deps"] = ["missing"]

        result = audit_payload({"cases": [changed]}, TRUTH, RAW)

        self.assertNotEqual(result["errors"], [])

    def test_raw_only_audit_rejects_five_preregistered_fault_mutations(self):
        case = {
            "case_id": "mutation_fixture",
            "provenance_complete": True,
            "current_versions": {"source": 1, "cfg": 2},
            "nodes": [
                {"id": "observe", "kind": "observe", "deps": [], "reads": {"source": 1}},
                {"id": "derive", "kind": "compute", "deps": ["observe"], "reads": {"cfg": 1}},
                {"id": "send", "kind": "effect", "deps": ["derive"],
                 "receipt": "ambiguous_delivery", "idempotent": True},
            ],
        }
        inputs = {"cases": [case]}
        truth = {"cases": {"mutation_fixture": copy.deepcopy(case)}}
        raw = {"results": [{"case_id": "mutation_fixture", "plan": plan_recovery(case)}]}

        result = mutation_suite(inputs, truth, raw)

        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["rejected"]), 5)


if __name__ == "__main__":
    unittest.main()
