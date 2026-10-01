from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
TRUTH = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))


class SameImageMethodTests(unittest.TestCase):
    def setUp(self):
        self.rows = candidate.build_rows(FIXTURE)

    def test_frozen_seven_case_method_matrix_passes_independent_audit(self):
        result = audit.audit(FIXTURE, TRUTH, self.rows)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["case_count"], 7)
        self.assertEqual(result["errors"], [])

    def test_denominator_drop_fails(self):
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, self.rows[:-1])["disposition"], "PASS_METHOD_SCOPED")

    def test_duplicate_case_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[-1] = copy.deepcopy(rows[0])
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, rows)["disposition"], "PASS_METHOD_SCOPED")

    def test_changed_image_identity_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["source_digest"] = "0" * 64
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, rows)["disposition"], "PASS_METHOD_SCOPED")

    def test_stale_action_authority_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[2]["action_authorized"] = True
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, rows)["disposition"], "PASS_METHOD_SCOPED")

    def test_trigger_miss_cannot_be_silently_deleted(self):
        rows = copy.deepcopy(self.rows)
        rows[4]["trigger"] = True
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, rows)["disposition"], "PASS_METHOD_SCOPED")

    def test_cost_underreporting_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[6]["cost_units"]["grounded_critique"] = 0
        self.assertNotEqual(audit.audit(FIXTURE, TRUTH, rows)["disposition"], "PASS_METHOD_SCOPED")

    def test_review_overhead_is_counted(self):
        row = next(r for r in self.rows if r["case_id"] == "no-error-overhead")
        self.assertGreater(row["cost_units"]["blind_reread"] + row["cost_units"]["grounded_critique"], 0)

    def test_same_bytes_at_new_epoch_is_not_hidden_state_or_authority(self):
        row = next(r for r in self.rows if r["case_id"] == "same-bytes-new-epoch")
        self.assertEqual(row["recapture_epoch"], 41)
        self.assertEqual(row["recommendation"], "NEW_EPOCH_SAME_PIXELS_NO_HIDDEN_STATE_CLAIM")
        self.assertFalse(row["action_authorized"])


if __name__ == "__main__":
    unittest.main()
