import json
import unittest
from pathlib import Path

import auditor
import candidate
from build_scenarios import scenarios


class FrameQualifiedCollateralTests(unittest.TestCase):
    def test_eleven_frozen_scenarios_four_policies_and_cost_gate(self):
        inputs = scenarios()
        result = candidate.run(inputs)
        audit = auditor.audit(inputs, result)
        self.assertEqual(len(inputs["cases"]), 11)
        self.assertEqual(len(result["rows"]), 44)
        self.assertEqual(audit["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(audit["cost_gate"], "PASS")
        self.assertEqual(audit["unsafe_qualified_frame_clean_cases"], [])
        self.assertGreaterEqual(audit["eligible_disjoint_accounted_byte_reduction_fraction"], 0.10)

    def test_full_oracle_catches_transitive_collateral_missed_by_controls(self):
        inputs = scenarios()
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(inputs)["rows"]}
        for policy in ("TARGET_ONLY", "STATIC_DIRECT"):
            self.assertEqual(rows[("transitive_formula_collateral", policy)]["verdict"], "CLEAN")
        for policy in ("FULL_STATE", "QUALIFIED_FRAME"):
            self.assertEqual(rows[("transitive_formula_collateral", policy)]["verdict"],
                             "COLLATERAL_CHANGED")

    def test_ineligible_frames_fallback_to_full_state(self):
        inputs = scenarios()
        rows = {(r["case_id"], r["policy"]): r for r in candidate.run(inputs)["rows"]}
        for case_id in ("alias_write", "hidden_callback_write", "external_writer_change",
                        "stale_generation", "delayed_durable_save", "missing_dependency_edge"):
            row = rows[(case_id, "QUALIFIED_FRAME")]
            self.assertEqual(row["metrics"]["fallback"], "FULL_STATE")
            self.assertEqual(row["verdict"], rows[(case_id, "FULL_STATE")]["verdict"])

    def test_mutated_frame_qualification_cannot_hide_an_alias(self):
        inputs = scenarios()
        case = next(c for c in inputs["cases"] if c["case_id"] == "alias_write")
        case["metadata"]["alias_edges"] = []
        case["metadata"]["alias_inventory_complete"] = True
        candidate_rows = candidate.run(inputs)
        audit = auditor.audit(inputs, candidate_rows)
        self.assertEqual(audit["status"], "FAIL_METHOD")
        self.assertIn("alias_write", audit["unsafe_qualified_frame_clean_cases"])

    def test_mutated_missing_dependency_and_writer_closure_are_detected(self):
        for case_id, field, value in (
            ("missing_dependency_edge", "dependency_inventory_complete", True),
            ("hidden_callback_write", "callback_inventory_complete", True),
            ("external_writer_change", "external_writers", []),
        ):
            with self.subTest(case_id=case_id):
                inputs = scenarios()
                case = next(c for c in inputs["cases"] if c["case_id"] == case_id)
                case["metadata"][field] = value
                if field == "callback_inventory_complete":
                    case["metadata"]["callbacks"] = []
                if field == "external_writers":
                    case["metadata"]["external_writer_inventory_complete"] = True
                result = candidate.run(inputs)
                audit = auditor.audit(inputs, result)
                self.assertEqual(audit["status"], "FAIL_METHOD")
                self.assertIn(case_id, audit["unsafe_qualified_frame_clean_cases"])

    def test_cost_and_virtual_read_counts_are_independently_reconstructed(self):
        inputs = scenarios()
        result = candidate.run(inputs)
        mutated = json.loads(json.dumps(result))
        mutated["rows"][0]["metrics"]["accounted_bytes"] += 1
        audit = auditor.audit(inputs, mutated)
        self.assertIn("accounted_bytes_mismatch:isolated_target_write:TARGET_ONLY", audit["errors"])

    def test_unqualified_case_cannot_be_silently_promoted_without_full_fallback(self):
        inputs = scenarios()
        result = candidate.run(inputs)
        row = next(r for r in result["rows"] if r["case_id"] == "stale_generation"
                   and r["policy"] == "QUALIFIED_FRAME")
        row["metrics"]["fallback"] = None
        audit = auditor.audit(inputs, result)
        self.assertIn("fallback_mismatch:stale_generation:QUALIFIED_FRAME", audit["errors"])

    def test_corrupt_event_manifest_is_rejected_and_full_oracle_remains_available(self):
        inputs = scenarios()
        case = inputs["cases"][0]
        case["events"][1]["new_value"] = 99
        result = candidate.run(inputs)
        row = next(r for r in result["rows"] if r["case_id"] == case["case_id"]
                   and r["policy"] == "QUALIFIED_FRAME")
        self.assertEqual(row["metrics"]["fallback"], "FULL_STATE")
        audit = auditor.audit(inputs, result)
        self.assertIn(f"event_state_mismatch:{case['case_id']}", audit["errors"])

    def test_timing_is_recorded_but_not_promoted_to_app_latency(self):
        rows = candidate.run(scenarios())["rows"]
        self.assertTrue(all(r["wall_time_median_ns_31"] > 0 for r in rows))


if __name__ == "__main__":
    unittest.main()
