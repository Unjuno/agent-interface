import unittest

import candidate


class ScheduleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = __import__("json").loads(candidate.FIXTURE_PATH.read_text())
        cls.trace = candidate.build(cls.fixture)

    def test_same_source_ledger_and_expected_update_cadence(self):
        ids = [episode["id"] for episode in self.fixture["episodes"]]
        self.assertEqual(self.trace["source_episode_ids"], ids)
        self.assertEqual({arm: len(value["updates"]) for arm, value in self.trace["schedules"].items()},
                         {"episodic_only": 0, "per_episode": 12, "batch_4": 3, "terminal": 1})
        self.assertEqual({arm: len(value["query_visibility"]) for arm, value in self.trace["schedules"].items()},
                         {arm: 16 for arm in candidate.SCHEDULES})

    def test_batch_and_terminal_expose_only_committed_prefix(self):
        rows = self.trace["schedules"]["batch_4"]["query_visibility"]
        at_three = [row for row in rows if row["checkpoint"] == 3]
        at_six = [row for row in rows if row["checkpoint"] == 6]
        self.assertTrue(all(row["latest_update_prefix"] is None and not row["available_episode_ids"] for row in at_three))
        self.assertTrue(all(row["latest_update_prefix"] == 4 and row["available_episode_ids"] == [
            episode["id"] for episode in self.fixture["episodes"][:4]] for row in at_six))
        terminal = self.trace["schedules"]["terminal"]["query_visibility"]
        before = [row for row in terminal if row["checkpoint"] < 12]
        self.assertTrue(all(row["latest_update_prefix"] is None and not row["available_episode_ids"] for row in before))

    def test_no_cross_schedule_or_source_mutation(self):
        self.assertEqual(len(set(self.trace["source_episode_sha256"].values())), 12)
        for arm in self.trace["schedules"].values():
            self.assertTrue(all(update["after_episode"] == len(update["episode_refs"]) for update in arm["updates"]))


if __name__ == "__main__":
    unittest.main()
