"""Probe whether the retained auditor binds decision inputs to raw calibration."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from audit import audit


FORMAL = Path(os.environ.get(
    "EC2766_FORMAL_ROOT",
    Path(__file__).resolve().parent / "restored" / "formal",
))


class CalibrationBindingProbe(unittest.TestCase):
    def test_original_wrong_g_source_mutation_is_still_accepted(self):
        with tempfile.TemporaryDirectory(prefix="2766-calibration-binding-") as td:
            root = Path(td) / "formal"
            shutil.copytree(FORMAL, root)
            path = next(root.glob("batch-*/*active_run_low_p/result.json"))
            record = json.loads(path.read_text(encoding="utf-8"))
            decision = record["decisions"][0]
            raw_median_g = record["calibration"]["wait_measure"]["median_ns"]
            self.assertEqual(decision["g_ns"], raw_median_g)
            self.assertEqual(decision["disposition"], "RUN")

            # Replay the original #2766 wrong_g mutation: alter only the copied
            # decision input. It preserves the mathematically correct RUN.
            decision["g_ns"] += 999_999_999
            self.assertNotEqual(decision["g_ns"], raw_median_g)
            self.assertEqual(decision["disposition"], "RUN")
            path.write_text(json.dumps(record), encoding="utf-8")

            observed = audit(root)
            # This passing assertion documents the current gap: the frozen
            # auditor accepts a decision input not bound to its raw median.
            self.assertEqual(observed["errors"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
