#!/usr/bin/env python3
"""Pre-freeze construction and four raw semantic corruption controls."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import audit

ROOT = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self.tmp.name) / "study"
        shutil.copytree(ROOT / "raw", self.copy / "raw")
        shutil.copy2(ROOT / "manifest.json", self.copy / "manifest.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def manifest(self) -> dict:
        return json.loads((self.copy / "manifest.json").read_text())

    def update(self, row: dict, data: bytes) -> None:
        (self.copy / row["file"]).write_bytes(data)
        manifest = self.manifest()
        target = next(r for r in manifest["arms"] if r["file"] == row["file"])
        target["sha256"] = hashlib.sha256(data).hexdigest()
        target["bytes"] = len(data)
        target["cue_offset"] = data.index(b"CURRENT_CUE:")
        (self.copy / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))

    def choose(self, arm: str, depth: int = 4) -> tuple[dict, bytes]:
        row = next(r for r in self.manifest()["arms"] if r["arm"] == arm and r["depth"] == depth and r["query"] == "CURRENT_VALUE")
        return row, (self.copy / row["file"]).read_bytes()

    def test_clean_fixture_passes(self) -> None:
        self.assertEqual([], audit.audit_path(self.copy))

    def test_final_truth_mutation_rejected_even_after_hash_refresh(self) -> None:
        row, data = self.choose("CURRENT_ONLY")
        self.update(row, data.replace(b"value-final-4", b"value-false-4", 1))
        self.assertIn("CURRENT_CUE_TRUTH", audit.audit_path(self.copy))

    def test_matched_cue_move_rejected_even_after_hash_refresh(self) -> None:
        row, data = self.choose("CURRENT_ONLY")
        offset = data.index(b"CURRENT_CUE:")
        self.update(row, data[:offset] + b"x" + data[offset:])
        self.assertIn("FROZEN_CUE_POSITION", audit.audit_path(self.copy))

    def test_drop_episode_without_lineage_rejected_even_after_hash_refresh(self) -> None:
        row, data = self.choose("SOURCE_LINKED_DELTA")
        slot_end = data.index(b"\n")
        history = json.loads(data[:slot_end])
        history.pop(1)
        slot = json.dumps(history, sort_keys=True, separators=(",", ":")).encode()
        budget = slot_end
        self.update(row, slot + b" " * (budget - len(slot)) + data[slot_end:])
        self.assertIn("HISTORY_DEPTH", audit.audit_path(self.copy))

    def test_inferred_delta_relabel_rejected_even_after_hash_refresh(self) -> None:
        row, data = self.choose("SOURCE_LINKED_DELTA")
        slot_end = data.index(b"\n")
        history = json.loads(data[:slot_end])
        history[0]["evidence_kind"] = "INFERRED"
        slot = json.dumps(history, sort_keys=True, separators=(",", ":")).encode()
        budget = slot_end
        self.update(row, slot + b" " * (budget - len(slot)) + data[slot_end:])
        self.assertIn("DELTA_LINEAGE", audit.audit_path(self.copy))


if __name__ == "__main__":
    unittest.main(verbosity=2)
