"""Mutation controls for the independent raw-stream audit of PR #7599."""
import copy
import hashlib
from pathlib import Path
import unittest

from .audit_raw_samples import (
    RUN,
    action_reconstruction,
    read_json,
    read_jsonl,
    release_order_ok,
    run_audit,
    validate_source_records,
)


class RawSamplingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_jsonl(RUN / "scorer-last-action.jsonl")
        cls.events = read_jsonl(RUN / "runtime/events.jsonl")
        cls.saved = read_json(RUN / "SAVED_ACTION_AUDIT.json")
        cls.result = run_audit()

    def test_independent_reconstruction_matches_frozen_selected_rows(self):
        self.assertTrue(all(self.cls_checks().values()))
        self.assertEqual(len(self.rows), 717)
        self.assertEqual(self.result["active_sample_count"], 8)
        self.assertEqual(self.result["active_sample_tics"], [1375, 1376, 1377, 1379, 1380, 1381, 1382, 1383])
        self.assertEqual(self.saved["sample_count"], self.result["action_sample_count"])

    def test_manifest_and_source_provenance_are_recomputed(self):
        self.assertTrue(self.result["checks"]["package_manifest_89_members"])
        self.assertTrue(self.result["checks"]["source_preparation_git_pins"])
        self.assertTrue(self.result["checks"]["source_preparation_sha256_and_byte_counts"])
        self.assertTrue(self.result["checks"]["declared_source_copies"])

    def test_wrong_source_sha256_claim_is_rejected(self):
        data = b"pinned source bytes"
        members = {"research/example.py": {
            "git_blob": "abc123", "sha256": "0" * 64, "bytes": len(data)
        }}
        checks = validate_source_records(members, {"research/example.py": "abc123"}, {b"abc123": data})
        self.assertEqual(checks["git_blob_failures"], [])
        self.assertEqual(checks["byte_count_failures"], [])
        self.assertEqual(checks["sha256_failures"], ["research/example.py"])

    def test_wrong_source_byte_count_claim_is_rejected(self):
        data = b"pinned source bytes"
        members = {"research/example.py": {
            "git_blob": "abc123", "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data) + 1,
        }}
        checks = validate_source_records(members, {"research/example.py": "abc123"}, {b"abc123": data})
        self.assertEqual(checks["git_blob_failures"], [])
        self.assertEqual(checks["sha256_failures"], [])
        self.assertEqual(checks["byte_count_failures"], ["research/example.py"])

    def test_static_result_is_exact_auditor_output(self):
        saved = read_json(Path(__file__).with_name("RESULT.json"))
        self.assertEqual(self.result, saved)

    def test_wrong_button_mutation_is_rejected(self):
        changed = copy.deepcopy(self.rows)
        active = next(i for i, row in enumerate(changed) if any(row["action"]))
        changed[active]["action"][1] = 1.0
        summary = action_reconstruction(changed)
        self.assertFalse(summary["checks"]["one_left_vector"])

    def test_keyup_after_neutral_sample_is_rejected(self):
        last_active = self.rows[max(i for i, row in enumerate(self.rows) if any(row["action"]))]
        first_neutral = self.rows[max(i for i, row in enumerate(self.rows) if any(row["action"])) + 1]
        release = next(e for e in self.events if e.get("event") == "input_release_transition")
        changed = copy.deepcopy(release)
        changed["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = first_neutral["sample_started_ns"] + 1
        self.assertFalse(release_order_ok(last_active, changed, first_neutral))

    def test_task_effect_and_useful_recovery_are_not_inferred(self):
        self.assertTrue(self.result["checks"]["progress_samples_linked_and_no_task_effect"])
        self.assertEqual(self.result["disposition"]["useful_game_effect_or_recovery"], "NOT_DEMONSTRATED")
        self.assertEqual(self.result["disposition"]["protocol_completion"], "STOP_PROTOCOL_COMPLETION")

    @classmethod
    def cls_checks(cls):
        return cls.result["checks"]


if __name__ == "__main__":
    unittest.main()
