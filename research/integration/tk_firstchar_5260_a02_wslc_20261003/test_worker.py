import json
import subprocess
import sys
import unittest
import candidate


class WorkerTests(unittest.TestCase):
    def test_worker_reports_actual_bounded_clock_span(self):
        self.assertTrue(hasattr(candidate, "worker_code"), "worker clock receipts missing")
        process = subprocess.run([sys.executable, "-c", candidate.worker_code(0.02)],
                                 capture_output=True, text=True, check=True)
        span = json.loads(process.stdout)
        self.assertGreaterEqual(span["end_ns"] - span["start_ns"], 15_000_000)
        self.assertLess(span["end_ns"] - span["start_ns"], 2_000_000_000)


if __name__ == "__main__":
    unittest.main()
