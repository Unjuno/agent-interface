import copy
import unittest

from audit_completeness import SCHEDULES, audit


def valid_raw():
    return {
        "mode": "formal",
        "rows": [
            {"schedule": schedule, "rep": rep, "index": index}
            for schedule in sorted(SCHEDULES)
            for rep in (10, 11)
            for index in range(8)
        ],
    }


class CompletenessAuditTests(unittest.TestCase):
    def test_exact_denominator_passes(self):
        self.assertEqual(audit(valid_raw())["decision"], "PASS_EXACT_FORMAL_DENOMINATOR")

    def test_missing_row_rejected(self):
        raw = valid_raw()
        raw["rows"].pop()
        self.assertIn("row_count", audit(raw)["errors"])

    def test_duplicate_rejected(self):
        raw = valid_raw()
        raw["rows"][-1] = copy.deepcopy(raw["rows"][0])
        self.assertIn("duplicate", audit(raw)["errors"])

    def test_unknown_schedule_rejected_even_at_same_denominator(self):
        raw = valid_raw()
        for row in raw["rows"]:
            if row["schedule"] == "STABLE_BASE":
                row["schedule"] = "UNREGISTERED"
        result = audit(raw)
        self.assertIn("schedule", result["errors"])
        self.assertIn("coverage", result["errors"])

    def test_wrong_repetition_rejected(self):
        raw = valid_raw()
        for row in raw["rows"]:
            if row["rep"] == 10:
                row["rep"] = 12
        result = audit(raw)
        self.assertIn("repetition", result["errors"])
        self.assertIn("coverage", result["errors"])

    def test_wrong_index_rejected(self):
        raw = valid_raw()
        raw["rows"][0]["index"] = 8
        result = audit(raw)
        self.assertIn("index", result["errors"])
        self.assertIn("coverage", result["errors"])


if __name__ == "__main__":
    unittest.main()
