import unittest

import audit
import candidate
from fixture_helper import load_inputs


class CorrectedAnalogyMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.fixture, cls.truth = load_inputs()

    def test_expected_exposure_and_schedules(self):
        raw = candidate.run(self.fixture)
        self.assertEqual(len(raw["rows"]), 72)
        self.assertEqual(len(raw["schedules"]), 6)
        self.assertEqual(len(raw["changed_schedules"]), 6)
        self.assertEqual(audit.inspect(raw, self.fixture, self.truth), [])

    def test_every_candidate_gets_the_same_fresh_checks_across_arms(self):
        raw = candidate.run(self.fixture)
        groups = {}
        for row in raw["rows"]:
            groups.setdefault((row["schedule_id"], row["candidate_id"]), []).append(row)
        self.assertTrue(all(len(rows) == 3 for rows in groups.values()))
        for rows in groups.values():
            self.assertEqual(len({str(row["common_checks"]) + row["common_status"] for row in rows}), 1)
            self.assertEqual({row["lookup_count"] for row in rows}, {1})
            self.assertEqual({row["review_slot_count"] for row in rows}, {1})
            self.assertEqual({row["context_word_count"] for row in rows}, {64})

    def test_scoped_memory_reopens_every_changed_envelope_control(self):
        raw = candidate.run(self.fixture)
        changed = [row for row in raw["rows"] if row["target_version"] == "v2" and
                   row["condition"] == "structured_memory"]
        self.assertEqual(len(changed), 6)
        self.assertTrue(all(row["decision"] == "PROPOSE" for row in changed))

    def test_candidate_metrics_and_independent_mutation_controls(self):
        raw = candidate.run(self.fixture)
        result = audit.audit(raw, self.fixture, self.truth)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["metrics"]["invalid_proposals_unchanged_envelope"],
                         {"no_memory": 6, "prose_memory": 6, "structured_memory": 0})
        self.assertEqual(result["metrics"]["valid_candidate_recall"]["structured_memory"],
                         {"proposed": 12, "eligible": 12})
        self.assertEqual(result["mutations_rejected"], 5)


if __name__ == "__main__":
    unittest.main()
