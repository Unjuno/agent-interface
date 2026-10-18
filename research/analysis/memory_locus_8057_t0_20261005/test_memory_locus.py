import copy
import json
import unittest
from pathlib import Path

from candidate import run
from audit import audit, oracle


FIXTURE = json.loads(Path("fixture.json").read_text(encoding="utf-8"))


class MemoryLocusTests(unittest.TestCase):
    def setUp(self):
        self.rows = run(FIXTURE)

    def test_independent_oracle_reconstructs_every_arm_step(self):
        self.assertEqual(len(self.rows), 96)
        self.assertEqual(audit(FIXTURE, self.rows), (True, "accepted"))
        self.assertEqual(len(oracle(FIXTURE)), 96)

    def test_environment_and_private_locus_cross_over_in_frozen_regimes(self):
        def total(case_id, arm):
            return sum(r["total_cost"] for r in self.rows if r["case_id"] == case_id and r["arm"] == arm)
        self.assertLess(total("repeat-stable-visible", "ENVIRONMENT_CUE"),
                        total("repeat-stable-visible", "PRIVATE_NOTE"))
        self.assertLess(total("repeat-app-generation-change", "PRIVATE_NOTE"),
                        total("repeat-app-generation-change", "ENVIRONMENT_CUE"))

    def test_stale_note_never_becomes_information(self):
        rows = [r for r in self.rows if r["case_id"] == "stale-private-note" and r["arm"] == "PRIVATE_NOTE"]
        self.assertTrue(all(r["source"] == "SAFE_REDISCOVERY" for r in rows))

    def test_unavailable_cue_never_becomes_information(self):
        rows = [r for r in self.rows if r["case_id"] == "repeat-obscured-cue" and r["arm"] == "ENVIRONMENT_CUE"]
        self.assertTrue(all(r["source"] == "SAFE_REDISCOVERY" for r in rows))

    def test_no_information_cue_does_not_replace_common_observation(self):
        rows = [r for r in self.rows if r["case_id"] == "cue-no-new-information" and r["arm"] == "ENVIRONMENT_CUE"]
        self.assertTrue(all(r["source"] == "COMMON_OBSERVATION" and r["cost"]["rediscovery"] == 0 for r in rows))

    def test_warning_visibility_and_restoration_are_hard_separate_gates(self):
        hidden = [r for r in self.rows if r["case_id"] == "warning-hidden-by-cue" and r["arm"] == "ENVIRONMENT_CUE"]
        self.assertTrue(all(r["task_correct"] and not r["warning_visible"] and not r["safety_pass"] for r in hidden))
        failed = [r for r in self.rows if r["case_id"] == "restoration-failure" and r["arm"] == "ENVIRONMENT_CUE"]
        self.assertTrue(all(r["task_correct"] and not r["restoration_ok"] and not r["safety_pass"] for r in failed))

    def test_mutation_using_stale_note_is_rejected(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "stale-private-note" and r["arm"] == "PRIVATE_NOTE")
        row["source"] = "PRIVATE_NOTE"
        self.assertFalse(audit(FIXTURE, mutated)[0])

    def test_mutation_treating_hidden_cue_as_present_is_rejected(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "repeat-obscured-cue" and r["arm"] == "ENVIRONMENT_CUE")
        row["source"] = "ENVIRONMENT_CUE"
        self.assertFalse(audit(FIXTURE, mutated)[0])

    def test_mutation_hiding_warning_is_not_averaged_into_cost(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "warning-hidden-by-cue" and r["arm"] == "ENVIRONMENT_CUE")
        row["safety_pass"] = True
        self.assertFalse(audit(FIXTURE, mutated)[0])

    def test_mutation_dropping_cost_component_is_rejected(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "repeat-stable-visible" and r["arm"] == "ENVIRONMENT_CUE")
        row["total_cost"] -= row["cost"]["ui_setup"]
        self.assertFalse(audit(FIXTURE, mutated)[0])

    def test_mutation_ignoring_restore_failure_is_rejected(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "restoration-failure" and r["arm"] == "ENVIRONMENT_CUE")
        row["restoration_ok"] = True
        self.assertFalse(audit(FIXTURE, mutated)[0])

    def test_both_channels_failed_uses_safe_rediscovery_or_stays_unresolved(self):
        ok = [r for r in self.rows if r["case_id"] == "both-channels-fail" and r["arm"] == "BOTH"]
        fail = [r for r in self.rows if r["case_id"] == "both-fail-no-rediscovery" and r["arm"] == "BOTH"]
        self.assertTrue(all(r["source"] == "SAFE_REDISCOVERY" and r["task_correct"] for r in ok))
        self.assertTrue(all(r["source"] == "UNRESOLVED" and not r["task_correct"] for r in fail))

    def test_mutation_fabricating_success_when_both_channels_fail_is_rejected(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "both-fail-no-rediscovery" and r["arm"] == "BOTH")
        row["source"] = "PRIVATE_NOTE"
        row["task_correct"] = True
        self.assertFalse(audit(FIXTURE, mutated)[0])


if __name__ == "__main__":
    unittest.main()
