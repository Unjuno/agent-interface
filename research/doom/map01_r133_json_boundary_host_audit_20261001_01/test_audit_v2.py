from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import audit_v2

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "construction-01"


class ExactPayloadAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_freeze_bytes = (HERE / "FREEZE.json").read_bytes()
        cls.original_freeze = json.loads(cls.original_freeze_bytes)
        cls.raw_bytes = (OUT / "RAW.json").read_bytes()
        cls.raw = json.loads(cls.raw_bytes)
        cls.run_receipt = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
        cls.freeze = {
            "main_sha": cls.original_freeze["main_sha"],
            "pinned_sha256": cls.original_freeze["pinned_sha256"],
        }

    def test_retained_payload_matches_full_independent_reconstruction(self):
        self.assertEqual(
            audit_v2.audit_bundle(self.raw, self.run_receipt, self.raw_bytes,
                                  self.freeze, self.original_freeze_bytes),
            [],
        )
        expected = audit_v2.expected_cases()
        observed = {row["case_id"]: json.loads(row["wire_json"])
                    for row in self.raw["cases"]}
        self.assertEqual(observed, expected)

    def test_collateral_payload_edit_is_rejected_after_resealing(self):
        altered = copy.deepcopy(self.raw)
        item = next(row for row in altered["cases"] if row["case_id"] == "pair_id_bool")
        item["parsed_rows"][0]["health_loss"] = 1
        item["wire_json"] = audit_v2.canonical(item["parsed_rows"])
        raw_bytes, run = audit_v2.reseal(altered, self.run_receipt)
        errors = audit_v2.audit_bundle(altered, run, raw_bytes,
                                       self.freeze, self.original_freeze_bytes)
        self.assertIn("wire_payload_not_exact:pair_id_bool", errors)
        self.assertIn("parsed_payload_not_exact:pair_id_bool", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
