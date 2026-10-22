"""Mutation controls for the supplemental per-key cleanup raw audit."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from audit_v2 import audit_raw

HERE = Path(__file__).resolve().parent
RAW = HERE / "fixtures" / "candidate-events.jsonl"
RESULT = HERE / "fixtures" / "RESULT.json"


def encoded(rows):
    return b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for row in rows
    )


class AuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = RAW.read_bytes()
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))
        cls.rows = [json.loads(line) for line in cls.raw.splitlines() if line]

    def run_rows(self, rows):
        raw = encoded(rows)
        result = dict(self.result, raw_sha256=hashlib.sha256(raw).hexdigest())
        return audit_raw(raw, json.dumps(result).encode("utf-8"))

    def release(self, rows, index=0):
        cleanup = next(row for row in rows if row.get("event") == "owner_release")
        return cleanup["per_key_release_measurements"][index]

    def test_frozen_baseline_passes(self):
        report = audit_raw(self.raw, RESULT.read_bytes())
        self.assertEqual(report["disposition"], "PASS_RECONSTRUCTED_SCOPED")
        self.assertEqual(report["release_count"], 2)

    def test_false_pre_sample_down_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        self.release(rows)["pre_sample"]["down"] = False
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_unavailable_pre_sample_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        self.release(rows)["pre_sample"]["available"] = False
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_down_post_sample_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        self.release(rows)["post_sample"]["down"] = True
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_reversed_sample_timestamps_are_rejected(self):
        rows = copy.deepcopy(self.rows)
        release = self.release(rows)
        release["post_sample"]["started_ns"] = release["post_sample"]["finished_ns"] + 1
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_release_request_after_post_sample_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        release = self.release(rows)
        release["release_request_ns"] = release["post_sample"]["finished_ns"] + 1
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_sync_return_before_release_request_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        release = self.release(rows)
        release["sync_return_ns"] = release["release_request_ns"] - 1
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")

    def test_boolean_interval_endpoint_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        release = self.release(rows)
        release["bracket"]["physical_up_interval"][0] = True
        self.assertEqual(self.run_rows(rows)["disposition"], "FAIL_MISMATCH")


if __name__ == "__main__":
    unittest.main()
