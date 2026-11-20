import copy
import hashlib
import json
import unittest
from pathlib import Path

from audit_v2 import audit

RAW = Path(__file__).resolve().parents[1] / "candidate" / "RAW.json"


class PosthocAuditV2Tests(unittest.TestCase):
    def setUp(self):
        self.raw_bytes = RAW.read_bytes()
        self.raw_digest = hashlib.sha256(self.raw_bytes).hexdigest()
        self.raw = json.loads(self.raw_bytes)

    def assert_serialized_mutation_rejected(self, raw, checks):
        changed_bytes = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        changed_digest = hashlib.sha256(changed_bytes).hexdigest()
        self.assertNotEqual(changed_digest, self.raw_digest)
        self.assertEqual(changed_digest, hashlib.sha256(changed_bytes).hexdigest())
        parsed = json.loads(changed_bytes)
        result = audit(parsed)
        for name in checks:
            self.assertFalse(result["checks"][name], name)

    def test_retained_raw_passes_protocol_pinned_audit(self):
        self.assertEqual(audit(self.raw)["status"], "PASS_SOURCE_PINNED_QUEUE_PREFETCH")

    def test_consistent_keycode_39_mutation_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["fixture"]["keycode"] = 39
        for edge in raw["edges"]:
            edge["matched_event"]["detail"] = 39
            for key in ("event_rows", "queued_snapshot_before_select"):
                for row in edge[key]:
                    if row.get("matches"):
                        row["detail"] = 39
        self.assert_serialized_mutation_rejected(raw, (
            "protocol_keycode_a", "exact_protocol_edges", "preselect_target"))

    def test_target_missing_from_prefetch_snapshot_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target_prefetched_before_select"] = False
        raw["edges"][0]["queued_snapshot_before_select"] = []
        self.assertFalse(audit(raw)["checks"]["preselect_target"])

    def test_consistent_window_id_mutation_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["fixture"]["window_id"] = 2097153
        raw["fixture"]["focus_id"] = 2097153
        for edge in raw["edges"]:
            edge["matched_event"]["window_id"] = 2097153
            for key in ("event_rows", "queued_snapshot_before_select"):
                for row in edge[key]:
                    if row.get("matches"):
                        row["window_id"] = 2097153
        self.assert_serialized_mutation_rejected(raw, (
            "observed_window_id", "exact_protocol_edges", "preselect_target"))


if __name__ == "__main__":
    unittest.main()
