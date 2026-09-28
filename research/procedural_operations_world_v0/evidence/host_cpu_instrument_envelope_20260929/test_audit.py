import tempfile
import unittest
from pathlib import Path

from audit import audit


FRAME = """bench_requested_frames=10000
bench_executed_frames=10000
wall_seconds=1.000000
frames_per_second=10000.00
ms_per_frame=0.1000
state_hash=0123456789abcdef
"""
RESET = """bench_resets=100000
wall_seconds=2000.000000
resets_per_second=50.00
us_per_reset=20000.000
"""


class AuditTests(unittest.TestCase):
    def audit_text(self, frame: str = FRAME, reset: str = RESET):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame_path, reset_path = root / "frame.txt", root / "reset.txt"
            frame_path.write_text(frame, encoding="utf-8")
            reset_path.write_text(reset, encoding="utf-8")
            return audit(frame_path, reset_path)

    def test_accepts_exact_counts_and_reports_cost_envelope(self):
        result = self.audit_text()
        self.assertEqual(result["decision"], "HOLD_CPU_INSTRUMENT_COST")
        self.assertTrue(result["frame_within_16_667ms"])
        self.assertFalse(result["reset_within_16_667ms"])

    def test_rejects_wrong_frame_denominator(self):
        with self.assertRaisesRegex(ValueError, "count_mismatch"):
            self.audit_text(FRAME.replace("10000", "9999", 1))

    def test_rejects_nonfinite_timing(self):
        with self.assertRaisesRegex(ValueError, "invalid_finite_nonnegative"):
            self.audit_text(FRAME.replace("0.1000", "nan"))

    def test_rejects_invalid_state_hash(self):
        with self.assertRaisesRegex(ValueError, "invalid_state_hash"):
            self.audit_text(FRAME.replace("0123456789abcdef", "bad"))

    def test_rejects_duplicate_metric(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_empty_key"):
            self.audit_text(FRAME + "ms_per_frame=0.1\n")


if __name__ == "__main__":
    unittest.main()
