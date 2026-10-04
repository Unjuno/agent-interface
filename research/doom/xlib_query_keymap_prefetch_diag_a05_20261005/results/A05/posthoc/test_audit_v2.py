import copy
import json
import unittest
from pathlib import Path

from audit_v2 import audit

RAW = Path(__file__).resolve().parents[1] / "candidate" / "RAW.json"


class PosthocAuditV2Tests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(RAW.read_text())

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
        self.assertFalse(audit(raw)["checks"]["protocol_keycode_a"])
        self.assertFalse(audit(raw)["checks"]["exact_protocol_edges"])
        self.assertFalse(audit(raw)["checks"]["preselect_target"])

    def test_target_missing_from_prefetch_snapshot_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target_prefetched_before_select"] = False
        raw["edges"][0]["queued_snapshot_before_select"] = []
        self.assertFalse(audit(raw)["checks"]["preselect_target"])


if __name__ == "__main__":
    unittest.main()
