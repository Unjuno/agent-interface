"""Mutation controls for owner sample states and key-up bracket timing."""
import copy
import json
import unittest

import audit_a10


class CancelCleanupAuditA10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in
                    (audit_a10.SOURCE_OUT / "candidate-events.jsonl")
                    .read_text(encoding="utf-8").splitlines() if line]

    def test_retained_raw_has_complete_sample_and_operation_brackets(self):
        self.assertEqual(audit_a10.validate_raw(copy.deepcopy(self.rows)), [])

    def test_sample_state_and_availability_mutations_are_rejected(self):
        cases = (
            ("pre_sample", "down", False),
            ("post_sample", "down", True),
            ("pre_sample", "available", False),
            ("post_sample", "error", "query failed"),
        )
        for sample_name, field, value in cases:
            rows = copy.deepcopy(self.rows)
            cleanup = next(row for row in rows if row.get("event") == "owner_release")
            cleanup["per_key_release_measurements"][0][sample_name][field] = value
            errors = audit_a10.validate_raw(rows)
            with self.subTest(sample=sample_name, field=field):
                self.assertTrue(errors)

    def test_sample_interval_and_keyup_bracket_mutations_are_rejected(self):
        mutations = (
            lambda row: row["pre_sample"].update(started_ns=row["pre_sample"]["finished_ns"] + 1),
            lambda row: row.update(release_request_ns=row["post_sample"]["finished_ns"] + 1),
            lambda row: row.update(sync_return_ns=row["post_sample"]["finished_ns"] + 1),
            lambda row: row.update(bracket={**row["bracket"],
                                            "physical_up_interval": [0, 1]}),
        )
        for mutate in mutations:
            rows = copy.deepcopy(self.rows)
            cleanup = next(row for row in rows if row.get("event") == "owner_release")
            mutate(cleanup["per_key_release_measurements"][0])
            with self.subTest(mutation=mutate):
                self.assertTrue(audit_a10.validate_raw(rows))

    def test_down_press_operation_must_fit_sample_bracket(self):
        rows = copy.deepcopy(self.rows)
        admission = next(row for row in rows if row.get("event") == "input_admission")
        measurement = admission["physical_key_measurement"]
        measurement["press_request_ns"] = measurement["post_sample"]["finished_ns"] + 1
        self.assertTrue(audit_a10.validate_raw(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
