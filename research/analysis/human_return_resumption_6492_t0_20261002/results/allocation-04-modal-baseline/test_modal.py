from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import audit_modal
import candidate_modal


PACKAGE = Path(__file__).resolve().parents[2]
FIXTURE = PACKAGE / "fixture.json"


class ImmediateModalBaselineTests(unittest.TestCase):
    def test_immediate_modal_baseline_and_six_corruption_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate.json"
            candidate_modal.run(FIXTURE, output)
            result = audit_modal.run_controls(FIXTURE, output)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["audited_modal_rows"], 6)
        self.assertEqual(result["control_count"], 7)
        self.assertEqual(result["rejected_controls"], 7)

    def test_modal_arm_does_not_capture_or_authorize_a_return_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate.json"
            candidate_modal.run(FIXTURE, output)
            result = json.loads(output.read_text())
        self.assertEqual(result["row_count"], 6)
        for row in result["rows"]:
            self.assertEqual(row["underlying_view"], "overlay_without_snapshot_or_copy")
            self.assertIsNone(row["cue_display"])
            self.assertFalse(row["return_action_authorized"])
            self.assertFalse(row["correct_return_action_disclosed"])
            self.assertFalse(row["automatic_effect"])


if __name__ == "__main__":
    unittest.main()
