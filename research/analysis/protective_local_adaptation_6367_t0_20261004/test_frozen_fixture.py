import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import summarize


ROOT = Path(__file__).parent


class FrozenFixtureTests(unittest.TestCase):
    def test_all_scheduled_controls_are_retained_and_independently_classified(self):
        fixture = json.loads((ROOT / "fixture.json").read_text())
        events = json.loads((ROOT / "events.json").read_text())

        report = summarize(fixture["offers"], events)
        checked = audit(fixture, events, report)

        self.assertEqual(len(fixture["offers"]), 18)
        self.assertEqual(report["offer_count"], 18)
        self.assertEqual(report["pair_count"], 9)
        self.assertEqual(checked["status"], "PASS_AUDIT")
        self.assertEqual(checked["case_statuses"], fixture["expected_cases"])
        self.assertIsNone(report["post_policy_subgroup_effect"])
        selection = next(row for row in report["cases"] if row["case_id"] == "selection-trap")
        self.assertEqual(selection["paired_success_delta"], 0)
        self.assertEqual(selection["pair_count"], 2)


if __name__ == "__main__":
    unittest.main()
