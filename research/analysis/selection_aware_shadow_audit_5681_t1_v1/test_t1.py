import unittest

import audit
import candidate


class SelectionAwareShadowAuditTests(unittest.TestCase):
    def test_event_dependent_design_bias_and_exact_ht_expectation(self):
        result = candidate.build()
        case = result["cases"]["event_dependent"]
        self.assertEqual(case["full_prevalence"], "1/2")
        self.assertEqual(case["delivered_prevalence"], "0")
        self.assertEqual(case["ht_expected_prevalence"], "1/2")
        self.assertEqual(case["draw_count"], 16)

    def test_label_independent_null_calibrates_in_design_expectation(self):
        case = candidate.build()["cases"]["label_independent_null"]
        self.assertEqual(case["full_prevalence"], "1/2")
        self.assertEqual(case["ht_expected_prevalence"], "1/2")
        self.assertEqual(case["draw_count"], 256)

    def test_zero_inclusion_target_is_not_estimable_without_number(self):
        case = candidate.build()["cases"]["zero_inclusion"]
        self.assertEqual(case["status"], "NOT_ESTIMABLE")
        self.assertNotIn("ht_expected_prevalence", case)
        self.assertIn("zero_inclusion_target", case["reasons"])

    def test_uncaptured_transient_is_outside_estimand_and_not_estimated(self):
        case = candidate.build()["cases"]["uncaptured_transient"]
        self.assertEqual(case["status"], "OUT_OF_FRAME_NOT_ESTIMABLE")
        self.assertNotIn("ht_expected_prevalence", case)
        self.assertEqual(case["frame_size"], 8)
        self.assertEqual(case["out_of_frame_event_count"], 1)

    def test_independent_auditor_accepts_candidate_and_corruption_controls(self):
        result = candidate.build()
        audited = audit.audit(result)
        self.assertEqual(audited["status"], "PASS")
        self.assertEqual(audited["corruption_controls_passed"], 7)
        self.assertEqual(audited["errors"], [])

    def test_independent_auditor_rejects_changed_design_probability(self):
        result = candidate.build()
        result["cases"]["event_dependent"]["units"][0]["inclusion_probability"] = "1"
        audited = audit.audit(result)
        self.assertEqual(audited["status"], "FAIL")
        self.assertTrue(audited["errors"])

    def test_independent_auditor_rejects_wrong_design_identifier(self):
        result = candidate.build()
        result["design"] = "with_replacement"
        audited = audit.audit(result)
        self.assertEqual(audited["status"], "FAIL")
        self.assertTrue(audited["errors"])

    def test_independent_auditor_fails_closed_on_missing_scenario_table(self):
        result = candidate.build()
        del result["cases"]["event_dependent"]["draws"]
        audited = audit.audit(result)
        self.assertEqual(audited["status"], "FAIL")
        self.assertTrue(audited["errors"])

    def test_candidate_cli_emits_json(self):
        import json
        import subprocess
        import sys
        from pathlib import Path

        output = subprocess.check_output(
            [sys.executable, str(Path(candidate.__file__))], text=True
        )
        self.assertEqual(json.loads(output)["schema"], "selection-aware-shadow-audit-t1-v1")

    def test_raw_only_auditor_cli_reads_one_json_file(self):
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.json"
            raw.write_text(json.dumps(candidate.build()))
            output = subprocess.check_output(
                [sys.executable, str(Path(audit.__file__)), str(raw)], text=True
            )
        self.assertEqual(json.loads(output)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
