"""Independent audit mutation tests; use only the standard library plus the auditor."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit_result import audit

CASES = [
    (64, 64, "UNCHANGED", True),
    (64, 64, "ONE_CHANNEL_PIXEL_CHANGE", False),
    (1920, 1080, "UNCHANGED", True),
    (1920, 1080, "ONE_CHANNEL_PIXEL_CHANGE", False),
    (3840, 2160, "UNCHANGED", True),
    (3840, 2160, "ONE_CHANNEL_PIXEL_CHANGE", False),
]

def fixture():
    rows = []
    measurements = []
    for width, height, outcome, expected in CASES:
        rows.append({
            "width": width, "height": height, "channels": 4,
            "outcome": outcome, "expected_equal": expected,
            "cpu_equal": expected, "cuda_equal": expected,
            "input_pair_sha256": "a" * 64,
        })
        cpu = [100] * 25
        cuda = [200] * 25
        measurements.append({
            "width": width, "height": height, "outcome": outcome,
            "repeats_per_arm": 25, "cpu_ns": cpu, "cuda_end_to_end_ns": cuda,
            "cpu_median_ns": 100, "cuda_end_to_end_median_ns": 200,
            "cpu_p95_ns": 100, "cuda_end_to_end_p95_ns": 200,
        })
    return {
        "schema_version": 1,
        "allocation": "gpu-exact-frame-gate-1564-20260928-01",
        "host": {"device_count": 1, "torch_cuda_runtime": "12.1"},
        "exactness_cases": rows,
        "measurements": measurements,
        "large_size_cuda_wins_on_unchanged": False,
        "decision": "REJECT_GPU_FOR_HOST_RESIDENT_EXACT_O1_SCOPED",
    }

class AuditTests(unittest.TestCase):
    def inspect(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return audit(path)

    def test_valid_rejection_fixture_passes_integrity_audit(self):
        self.assertEqual(self.inspect(fixture())["result"], "PASS_RAW_RESULT_AUDIT")

    def test_stale_summary_is_rejected(self):
        value = fixture()
        value["measurements"][0]["cpu_median_ns"] = 99
        self.assertEqual(self.inspect(value)["result"], "FAIL_RAW_RESULT_AUDIT")

    def test_wrong_cuda_exactness_is_rejected(self):
        value = fixture()
        value["exactness_cases"][0]["cuda_equal"] = False
        self.assertEqual(self.inspect(value)["result"], "FAIL_RAW_RESULT_AUDIT")

if __name__ == "__main__":
    unittest.main(verbosity=2)
