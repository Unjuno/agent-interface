"""Audit regressions; all corruptions operate on copies of fixture rows."""
from __future__ import annotations

import copy
import unittest

from audit import audit_rows, reference_cases, reference_prediction, POLICIES
from gate import evaluate


class FrozenAuditTests(unittest.TestCase):
    @staticmethod
    def clean_rows():
        return [
            {"input": case, "predictions": {p: reference_prediction(case, p) for p in POLICIES}}
            for case in reference_cases()
        ]

    def test_positive_complete_corpus(self):
        self.assertEqual(audit_rows(self.clean_rows()), [])

    def test_eight_effective_copied_row_mutations_reject(self):
        mutations = [
            lambda row: row["input"].update(truth="NO_OP"),
            lambda row: row["input"].update(scores=[0.1, 0.2, 0.3]),
            lambda row: row["input"].update(times_ms=[0, 0, 200]),
            lambda row: row["input"].update(history_status="EPOCH_MISMATCH"),
            lambda row: row["input"].update(intent_id="foreign-intent"),
            lambda row: row["predictions"]["CURRENT_ONLY"].update(decision="YIELD"),
            lambda row: row["predictions"]["LEVEL_PLUS_VELOCITY"].update(source="CURRENT_ONLY"),
            lambda row: row["predictions"]["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"].update(features_used=[]),
        ]
        for mutate in mutations:
            rows = copy.deepcopy(self.clean_rows())
            mutate(rows[0])
            with self.subTest(mutation=mutate):
                self.assertTrue(audit_rows(rows))

    def test_frozen_first_rung_discriminator(self):
        rows = self.clean_rows()
        self.assertEqual(evaluate(rows)["disposition"], "PASS_SYNTHETIC_DISCRIMINATOR_ONLY")


if __name__ == "__main__":
    unittest.main()
