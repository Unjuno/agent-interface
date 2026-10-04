"""Boundary regressions for the A03 owner/adapter interval join gap."""
import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

HERE = Path(__file__).resolve().parent
A03_INPUT = (HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005"
             / "INPUT_EVENTS.jsonl")
EVENTS = [json.loads(line) for line in A03_INPUT.read_text(encoding="utf-8").splitlines()
          if line]


class ExactOwnerIntervalTests(unittest.TestCase):
    def test_retained_down_up_intervals_match_independent_reconstruction(self):
        expected = {"down": [87811364890958, 87811364895916],
                    "up": [87811364946333, 87811364949416]}
        self.assertEqual(candidate.owner_intervals(EVENTS), expected)
        self.assertEqual(audit.independently_reconstruct(EVENTS), expected)

    def test_equal_float_alias_in_down_or_up_owner_bracket_is_rejected(self):
        for row_index, field in ((0, "physical_down_interval"),
                                 (1, "physical_up_interval")):
            with self.subTest(row=row_index, field=field):
                rows = copy.deepcopy(EVENTS)
                interval = rows[row_index]["physical_key_measurement"]["bracket"][field]
                rows[row_index]["physical_key_measurement"]["bracket"][field] = [
                    float(interval[0]), interval[1]]
                with self.assertRaises(candidate.EvidenceError):
                    candidate.owner_intervals(rows)
                with self.assertRaises(ValueError):
                    audit.independently_reconstruct(rows)

    def test_equal_boolean_alias_in_owner_bracket_is_rejected(self):
        for row_index, field in ((0, "physical_down_interval"),
                                 (1, "physical_up_interval")):
            with self.subTest(row=row_index, field=field):
                rows = copy.deepcopy(EVENTS)
                interval = rows[row_index]["physical_key_measurement"]["bracket"][field]
                rows[row_index]["physical_key_measurement"]["bracket"][field] = [
                    True, interval[1]]
                with self.assertRaises(candidate.EvidenceError):
                    candidate.owner_intervals(rows)
                with self.assertRaises(ValueError):
                    audit.independently_reconstruct(rows)

    def test_integer_disagreement_and_malformed_interval_are_rejected(self):
        cases = ((0, "physical_down_interval", lambda iv: [iv[0] + 1, iv[1]]),
                 (1, "physical_up_interval", lambda iv: [iv[0]]))
        for row_index, field, mutate in cases:
            with self.subTest(row=row_index, field=field):
                rows = copy.deepcopy(EVENTS)
                interval = rows[row_index]["physical_key_measurement"]["bracket"][field]
                rows[row_index]["physical_key_measurement"]["bracket"][field] = mutate(interval)
                with self.assertRaises(candidate.EvidenceError):
                    candidate.owner_intervals(rows)
                with self.assertRaises(ValueError):
                    audit.independently_reconstruct(rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
