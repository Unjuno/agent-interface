"""Corruption tests for the retained Docker Desktop probe audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit import audit

REPO = Path(__file__).resolve().parents[4]
SOURCE = REPO / "research/doom/map01_model_loop_finite_v4/results/dockerdesktop-20260921-01"


class ProbeAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "evidence"
        shutil.copytree(SOURCE, self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def refresh_manifest(self) -> None:
        rows = []
        for name in ("raw.jsonl", "result.json"):
            digest = hashlib.sha256((self.root / name).read_bytes()).hexdigest()
            rows.append(f"{digest}  {name}\n")
        (self.root / "SHA256SUMS").write_text("".join(rows))

    def test_original_rows_validate_but_missing_child_exit_is_a_hold(self) -> None:
        result = audit(self.root, REPO)
        self.assertEqual(result["semantic_disposition"], "PASS_CONTROLS_AND_CLOCKS_SCOPED")
        self.assertEqual(result["disposition"], "HOLD_CONTAINER_EXIT_UNRECORDED")

    def test_duplicate_lease_control_is_rejected(self) -> None:
        raw = (self.root / "raw.jsonl").read_text().splitlines()
        duplicate = next(row for row in raw if '"kind": "lease"' in row)
        (self.root / "raw.jsonl").write_text("\n".join(raw + [duplicate]) + "\n")
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "lease-control row count"):
            audit(self.root, REPO)

    def test_result_control_summary_must_match_raw(self) -> None:
        result = json.loads((self.root / "result.json").read_text())
        result["controls"][0]["outcome"] = "forged"
        (self.root / "result.json").write_text(json.dumps(result))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "control summary/raw agreement"):
            audit(self.root, REPO)

    def test_clock_summary_must_match_raw(self) -> None:
        result = json.loads((self.root / "result.json").read_text())
        result["clock_bounds"]["max_bound_width_ns"] += 1
        (self.root / "result.json").write_text(json.dumps(result))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "clock summary/raw agreement"):
            audit(self.root, REPO)


if __name__ == "__main__":
    unittest.main()
