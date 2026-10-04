"""Mutation checks for decision-row validation, using only retained inputs."""
import copy
import unittest

from research.doom import audit_map01_astra_timeline_v1 as audit


class TimelineAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline, cls.report, cls.events, cls.visual = audit.load_inputs()

    def test_retained_result_passes(self):
        audit.audit(self.timeline, self.report, self.events, self.visual)

    def assert_mutation_rejected(self, mutate):
        changed = copy.deepcopy(self.timeline)
        mutate(changed)
        with self.assertRaises(AssertionError):
            audit.audit(changed, self.report, self.events, self.visual)

    def test_wrong_row_key_set_rejected(self):
        self.assert_mutation_rejected(lambda t: t["decisions"][3]["keys_held"][0]["keys"].append("Down"))

    def test_wrong_row_interval_count_rejected(self):
        self.assert_mutation_rejected(lambda t: t["decisions"][4].__setitem__("input_admission_count", 9))

    def test_wrong_row_observation_count_rejected(self):
        self.assert_mutation_rejected(lambda t: t["decisions"][6].__setitem__("observation_count", 40))

    def test_wrong_row_hud_join_rejected(self):
        self.assert_mutation_rejected(lambda t: t["decisions"][7].__setitem__("health_at_decision", 84))

    def test_wrong_release_count_rejected(self):
        self.assert_mutation_rejected(lambda t: t["decisions"][0].__setitem__("verified_release_count", 1))


if __name__ == "__main__":
    unittest.main()
