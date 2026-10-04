"""Mutation controls for the independent raw/target-dispatch join auditor."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from audit_target_dispatch_capture import (  # noqa: E402
    DispatchAuditError, audit,
)
from test_private_benchmark_channel import assemble_raw_from_private_channels  # noqa: E402


class TargetDispatchRawAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        (root / "channel").mkdir()
        cls.capture_path = root / "dispatch.json"
        cls.raw = assemble_raw_from_private_channels(root / "channel",
                                                     cls.capture_path)
        cls.capture = json.loads(cls.capture_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_full_raw_capture_joins_all_ordered_dispatches(self):
        result = audit(self.raw, self.capture)
        self.assertEqual(result, {"audit": "PASS_SYNTHETIC_DISPATCH_JOIN",
                                  "tasks_verified": 18,
                                  "target_dispatches_verified": 36})

    def test_reversed_target_order_is_rejected(self):
        capture = copy.deepcopy(self.capture)
        capture["arms"]["plain"][0]["target_results"].reverse()
        with self.assertRaisesRegex(DispatchAuditError, "target dispatch order"):
            audit(self.raw, capture)

    def test_stale_request_sequence_is_rejected(self):
        capture = copy.deepcopy(self.capture)
        capture["arms"]["ephemeral"][1]["target_results"][0]["request"][
            "expected_sequence"] -= 1
        with self.assertRaisesRegex(DispatchAuditError, "fresh raw observation"):
            audit(self.raw, capture)

    def test_missing_release_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["arms"]["plain"][0]["release_events"].pop()
        with self.assertRaisesRegex(DispatchAuditError, "ordered verified release"):
            audit(raw, self.capture)

    def test_b1_old_reference_admission_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["arms"]["persistent"][3]["input_events"][0]["status"] = "ADMITTED"
        raw["arms"]["persistent"][3]["input_events"][0]["admission_ns"] = (
            raw["arms"]["persistent"][3]["started_ns"] + 500)
        with self.assertRaisesRegex(DispatchAuditError, "raw admissions"):
            audit(raw, self.capture)

    def test_malformed_raw_observation_fails_closed(self):
        raw = copy.deepcopy(self.raw)
        raw["arms"]["ephemeral"][2]["observation_events"][1] = None
        with self.assertRaisesRegex(DispatchAuditError,
                                    "source observation sequence"):
            audit(raw, self.capture)


if __name__ == "__main__":
    unittest.main()
