from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.receipt import receipt_view


def state(**overrides):
    row = {
        "schema": "agent-interface/motor-state-v1",
        "state_id": "s1",
        "owner_id": "o1",
        "owner_revision": 1,
        "observation_id": "obs1",
        "surface_id": "surface1",
        "coordinate_frame": "screen",
        "commanded_pointer": {"x": 1, "y": 2},
        "observed_pointer": {"x": 1, "y": 2},
        "held_keys": [],
        "held_buttons": [],
        "input_ack": {"id": "a1", "status": "ACKED"},
        "release": {"status": "NOT_TERMINAL", "retained": True},
        "uncertainty": "NONE",
        "events": [],
    }
    row.update(overrides)
    return row


class ReceiptMotorStateTests(unittest.TestCase):
    def write(self, report):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "receipt.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return td, path

    def test_absent_state_is_explicit_and_legacy_shape_stays_read_only(self):
        td, path = self.write({"status": "completed", "records": []})
        with td:
            row = receipt_view(str(path))
        self.assertEqual(row["authority"], "none")
        self.assertEqual(row["motor_state_validation"], {"present": False, "accepted": False, "reason": "missing"})

    def test_accepted_state_is_only_validation_evidence(self):
        td, path = self.write({"status": "completed", "motor_state": state(), "records": []})
        with td:
            row = receipt_view(str(path))
        self.assertEqual(row["motor_state_validation"], {"present": True, "accepted": True, "reason": "ok"})
        self.assertEqual(row["authority"], "none")
        self.assertNotIn("dispatch", row["motor_state_validation"])

    def test_rejected_authority_bearing_state_fails_closed(self):
        td, path = self.write({"status": "completed", "motor_state": state(authority="granted"), "records": []})
        with td:
            row = receipt_view(str(path))
        self.assertEqual(row["motor_state_validation"]["accepted"], False)
        self.assertEqual(row["motor_state_validation"]["reason"], "unknown_or_authority_field")

    def test_raw_view_does_not_validate_or_mutate(self):
        report = {"status": "completed", "motor_state": state(), "records": []}
        td, path = self.write(report)
        with td:
            row = receipt_view(str(path), raw=True)
        self.assertEqual(row, report)


if __name__ == "__main__":
    unittest.main()
