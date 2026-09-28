"""Fresh construction controls for the two non-rejecting #2766 mutations.

These tests use copies of already-retained raw results. They never invoke the
formal runner or alter the restored source evidence.
"""
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


def result_for(root: Path, case: str) -> Path:
    return next(root.glob(f"batch-*/*{case}/result.json"))


class ControlTargetTests(unittest.TestCase):
    def make_copy(self):
        temp = tempfile.TemporaryDirectory(prefix="2766-control-target-")
        destination = Path(temp.name) / "formal"
        shutil.copytree(FORMAL, destination)
        self.addCleanup(temp.cleanup)
        return destination

    def test_wrong_g_changes_expected_selector_disposition(self):
        root = self.make_copy()
        path = result_for(root, "active_run_low_p")
        row = json.loads(path.read_text(encoding="utf-8"))
        decision = row["decisions"][0]
        self.assertEqual(decision["disposition"], "RUN")
        # Decrease g (rather than increase it): with p=1/4 and w>0,
        # p*w > (1-p)*g at g=0, so the oracle must select WAIT.
        decision["g_ns"] = 0
        path.write_text(json.dumps(row), encoding="utf-8")
        result = audit(root)
        self.assertTrue(any("RUN!=WAIT" in error for error in result["errors"]))

    def test_publish_after_cancel_targets_a_cancellation_case(self):
        root = self.make_copy()
        path = result_for(root, "active_compute_invalidation")
        row = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(any(d["disposition"] == "CANCEL_STALE"
                            for d in row["decisions"][1:]))
        row["published_reusable"] = True
        path.write_text(json.dumps(row), encoding="utf-8")
        result = audit(root)
        self.assertIn("published_after_cancel:active_compute_invalidation",
                      result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
