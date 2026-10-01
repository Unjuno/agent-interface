#!/usr/bin/env python3
"""Synthetic corruption controls for the Issue #4809 typed STOP auditor."""
import unittest

from stop_audit import ALLOCATION, validate


def record():
    return {
        "schema": "issue-4809-mitra-gpu-stop-v1",
        "allocation": ALLOCATION,
        "stage": "preflight",
        "exception_type": "RuntimeError",
        "exception": "synthetic construction fixture",
        "optimizer_step_calls": 0,
        "model_load_count": 0,
        "partial_query_count": 0,
        "partial_query_records": [],
        "start_unix_ns": 1,
        "stop_unix_ns": 2,
    }


class StopAuditControls(unittest.TestCase):
    def test_complete_typed_stop_passes(self):
        self.assertTrue(validate(record())["pass"])

    def test_wrong_allocation_is_rejected(self):
        bad = record()
        bad["allocation"] = "another-run"
        self.assertIn("allocation", validate(bad)["errors"])

    def test_partial_count_mismatch_is_rejected(self):
        bad = record()
        bad["partial_query_count"] = 1
        self.assertIn("partial_query_records", validate(bad)["errors"])

    def test_invalid_time_interval_is_rejected(self):
        bad = record()
        bad["stop_unix_ns"] = 0
        self.assertIn("time_interval", validate(bad)["errors"])


if __name__ == "__main__":
    unittest.main()
