"""Construction tests for independent raw-widget and event-log reconstruction."""

import copy
import importlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class IndependentRealTkAuditTests(unittest.TestCase):
    def test_auditor_reconstructs_raw_widget_effects_and_rejects_four_mutations(self):
        candidate_spec = importlib.util.find_spec("candidate")
        self.assertIsNotNone(candidate_spec, "candidate module is not implemented yet")
        audit_spec = importlib.util.find_spec("auditor")
        self.assertIsNotNone(audit_spec, "auditor module is not implemented yet")
        candidate_module = importlib.import_module("candidate")
        auditor_module = importlib.import_module("auditor")

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
        candidate = candidate_module.run(fixture)
        audited = auditor_module.audit(fixture, candidate, truth)
        self.assertEqual("PASS_METHOD_SCOPED", audited["disposition"])
        self.assertEqual({"pass": 4, "violation": 5, "unknown": 3, "not_applicable": 1}, audited["counts"])
        self.assertEqual([], audited["reconstruction_errors"])

        mutations = []
        changed_claim = copy.deepcopy(candidate)
        next(row for row in changed_claim["rows"] if row["id"] == "duplicate_callback")["status"] = "PASS"
        mutations.append((fixture, changed_claim, truth))

        changed_raw_state = copy.deepcopy(candidate)
        wrong_field_row = next(row for row in changed_raw_state["rows"] if row["id"] == "wrong_field")
        wrong_field_row["raw"]["widget_values"]["decoy"] = "wrong"
        wrong_field_row["replay_raw"]["widget_values"]["decoy"] = "wrong"
        mutations.append((fixture, changed_raw_state, truth))

        missing_callback = copy.deepcopy(candidate)
        duplicate_row = next(row for row in missing_callback["rows"] if row["id"] == "duplicate_callback")
        duplicate_row["raw"]["event_log"] = [
            event for event in duplicate_row["raw"]["event_log"]
            if event.get("effect") != "duplicate"
        ]
        mutations.append((fixture, missing_callback, truth))

        stale_digest = copy.deepcopy(candidate)
        stale_digest["input_sha256"] = "0" * 64
        mutations.append((fixture, stale_digest, truth))

        for mutated_fixture, mutated_candidate, mutated_truth in mutations:
            with self.assertRaises((ValueError, AssertionError)):
                auditor_module.audit(mutated_fixture, mutated_candidate, mutated_truth)


if __name__ == "__main__":
    unittest.main()
