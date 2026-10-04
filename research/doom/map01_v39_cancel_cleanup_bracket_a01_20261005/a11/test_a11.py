"""Mutation controls for duplicate cleanup records and explicit release integrity."""
import copy
import json
import unittest

import audit_a11


class CleanupIntegrityA11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [
            json.loads(line)
            for line in (audit_a11.SOURCE_OUT / "candidate-events.jsonl")
            .read_text(encoding="utf-8").splitlines() if line
        ]

    def test_retained_raw_passes_integrity_gate(self):
        self.assertEqual(audit_a11.validate_raw(copy.deepcopy(self.rows)), [])

    def test_duplicate_admission_row_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows.append(copy.deepcopy(rows[0]))
        self.assertTrue(audit_a11.validate_raw(rows))

    def test_duplicate_release_measurement_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        cleanup = next(row for row in rows if row.get("event") == "owner_release")
        cleanup["per_key_release_measurements"].append(
            copy.deepcopy(cleanup["per_key_release_measurements"][0])
        )
        self.assertTrue(audit_a11.validate_raw(rows))

    def test_release_not_attempted_or_missing_flag_is_rejected(self):
        for value in (False, None):
            rows = copy.deepcopy(self.rows)
            cleanup = next(row for row in rows if row.get("event") == "owner_release")
            measurement = cleanup["per_key_release_measurements"][0]
            if value is None:
                measurement.pop("release_attempted", None)
            else:
                measurement["release_attempted"] = value
            with self.subTest(value=value):
                self.assertTrue(audit_a11.validate_raw(rows))

    def test_actuation_ids_must_be_unique_across_keys(self):
        rows = copy.deepcopy(self.rows)
        admissions = [row for row in rows if row.get("event") == "input_admission"]
        cleanup = next(row for row in rows if row.get("event") == "owner_release")
        shared = admissions[0]["physical_key_measurement"]["actuation_id"]
        admissions[1]["physical_key_measurement"]["actuation_id"] = shared
        cleanup["per_key_release_measurements"][1]["actuation_id"] = shared
        self.assertTrue(audit_a11.validate_raw(rows))

    def test_malformed_unhashable_key_is_rejected_without_crashing(self):
        rows = copy.deepcopy(self.rows)
        admission = next(row for row in rows if row.get("event") == "input_admission")
        admission["key"] = {"unexpected": "object"}
        self.assertTrue(audit_a11.validate_raw(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
