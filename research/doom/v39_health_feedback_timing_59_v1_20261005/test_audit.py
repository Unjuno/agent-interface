import copy
import json
import unittest
from pathlib import Path

import audit


BASE = Path(__file__).resolve().parent


def frozen_blobs():
    freeze = json.loads((BASE / "FREEZE.json").read_text(encoding="utf-8"))
    paths = set(freeze["members"]) | {"retention-manifest.json"}
    blobs = {path: audit.source_blob(freeze["source_commit"], f"{freeze['allocation']}/{path}") for path in paths}
    return freeze, blobs


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze, cls.blobs = frozen_blobs()

    def test_recomputes_feedback_timing_and_release_boundary(self):
        result = audit.analyze(self.freeze, self.blobs)
        measured = result["measurements"]
        self.assertEqual(measured["feedback_to_outcome_ms"], 116.350394)
        self.assertEqual(measured["feedback_to_hold_step_completion_ms"], 96.311598)
        self.assertEqual(measured["feedback_to_next_step_keys_ack_ms"], 154.146074)
        self.assertEqual(measured["feedback_to_verified_empty_owner_release_ms"], 1937.087025)
        self.assertFalse(measured["normal_per_key_up_receipt_present"])

    def test_rejects_health_value_corruption(self):
        bad = copy.deepcopy(self.blobs)
        report = json.loads(bad["report.json"])
        report["decisions"][1]["cover_validity_latest_soft_event"]["signal"]["value"] = 84
        bad["report.json"] = json.dumps(report).encode()
        with self.assertRaisesRegex(audit.AuditError, "frozen SHA256 mismatch for report.json"):
            audit.analyze(self.freeze, bad)

    def test_rejects_event_outside_model_wait(self):
        bad = copy.deepcopy(self.blobs)
        report = json.loads(bad["report.json"])
        report["decisions"][1]["cover_validity_latest_soft_event"]["signal"]["capture_ns"] = 55520000000000
        bad["report.json"] = json.dumps(report).encode()
        with self.assertRaisesRegex(audit.AuditError, "frozen SHA256 mismatch for report.json"):
            audit.analyze(self.freeze, bad)

    def test_refuses_to_label_program_release_as_key_up_if_schema_grows(self):
        bad = dict(self.blobs)
        rows = [json.loads(line) for line in bad["runtime/events.jsonl"].splitlines()]
        rows.append({"event": "input_released", "id": "cover-1", "key": "a", "released_ns": 55516087720627})
        bad["runtime/events.jsonl"] = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(audit.AuditError, "frozen SHA256 mismatch for runtime/events.jsonl"):
            audit.analyze(self.freeze, bad)


if __name__ == "__main__":
    unittest.main()
