#!/usr/bin/env python3
"""Offline construction/mutation checks; these are not the formal allocation."""
import json
import pathlib
import shutil
import tempfile
import unittest

import auditor
import candidate


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name) / "out"
        candidate.build(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def clone(self):
        target = pathlib.Path(self.temp.name) / "copy"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.root, target)
        return target

    def test_clean_fixture_passes(self):
        result = auditor.audit_package(self.root)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual((result["matched_trials"], result["presentation_rows"], result["isolated_controls"]), (144, 288, 16))

    def test_changed_cue_pixel_rejected(self):
        copied = self.clone()
        p = next((copied / "images").iterdir())
        blob = bytearray(p.read_bytes())
        blob[-1] ^= 1
        p.write_bytes(blob)
        self.assertFalse(auditor.audit_package(copied)["ok"])

    def test_frame_order_and_source_index_rejected(self):
        copied = self.clone()
        p = copied / "presentations.jsonl"
        rows = [json.loads(x) for x in p.read_text().splitlines()]
        rows[0]["frames"][0], rows[0]["frames"][1] = rows[0]["frames"][1], rows[0]["frames"][0]
        rows[0]["source_indices"][0] = 1
        p.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
        self.assertFalse(auditor.audit_package(copied)["ok"])

    def test_truth_state_mutation_rejected(self):
        copied = self.clone()
        p = copied / "oracle.json"
        oracle = json.loads(p.read_text())
        oracle["rows"][0]["cue2"] = "green_triangle" if oracle["rows"][0]["cue2"] != "green_triangle" else "red_square"
        p.write_text(json.dumps(oracle, sort_keys=True, indent=2) + "\n")
        self.assertIn("oracle-mismatch", auditor.audit_package(copied)["errors"])

    def test_arm_mapping_mutation_rejected(self):
        copied = self.clone()
        p = copied / "presentations.jsonl"
        rows = [json.loads(x) for x in p.read_text().splitlines()]
        rows[0]["arm"] = "T2_ONLY" if rows[0]["arm"] == "DUAL_REQUIRED" else "DUAL_REQUIRED"
        p.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
        self.assertFalse(auditor.audit_package(copied)["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
