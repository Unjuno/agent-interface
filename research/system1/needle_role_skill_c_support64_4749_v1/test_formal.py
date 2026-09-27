"""Zero-fit tests for frozen Docker command bindings and allocation topology."""
import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path
import json

import formal


class FormalCommandTests(unittest.TestCase):
    def test_builder_injects_exact_seed_and_output(self):
        argv = formal.builder_argv("/workspace/src", "/workspace/out/seed-7865101", 7865101)
        self.assertIn("--env", argv)
        self.assertIn("NEEDLE_SEED=7865101", argv)
        self.assertIn("NEEDLE_OUTPUT=/out", argv)
        self.assertTrue(any("target=/src,readonly" in item for item in argv))
        self.assertTrue(any("target=/out" in item for item in argv))
        self.assertIn("none", argv)
        self.assertIn("--pull=never", argv)
        self.assertIn("--platform", argv)
        self.assertIn("linux/amd64", argv)

    def test_each_seed_arm_loader_has_unique_mounts(self):
        paths = set()
        for seed in formal.SEEDS:
            seed_out = f"/workspace/out/seed-{seed}"
            self.assertNotIn(seed_out, paths)
            paths.add(seed_out)
            for arm in formal.ARMS:
                for loader in ("load1", "load2"):
                    load_out = f"/workspace/out/seed-{seed}/{arm}/{loader}"
                    self.assertNotIn(load_out, paths)
                    paths.add(load_out)
                    argv = formal.loader_argv("/workspace/src", f"/workspace/out/seed-{seed}/builder/{arm}", load_out)
                    self.assertTrue(any("target=/src,readonly" in item for item in argv))
                    self.assertTrue(any("target=/pkg,readonly" in item for item in argv))
                    self.assertTrue(any("target=/load" in item for item in argv))
        self.assertEqual(len(formal.SEEDS), len(set(formal.SEEDS)))

    def test_seeds_are_spaced_beyond_all_documented_offsets(self):
        self.assertTrue(all(b - a == 100 for a, b in zip(formal.SEEDS, formal.SEEDS[1:])))
        streams = {seed + offset for seed in formal.SEEDS for offset in range(13)}
        self.assertEqual(len(streams), len(formal.SEEDS) * 13)
        self.assertNotIn(7865001, streams)

    def test_formal_stops_before_marker_without_verified_github_and_collision_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            out = Path(tmp) / "out"
            source.mkdir()
            freeze = {"allocation": "needle-role-skill-c-support64-4749-v1",
                      "formal_seeds": list(formal.SEEDS), "image_id": formal.IMAGE_ID,
                      "source_sha256": {}, "github_readback": {}, "collision_audit": {}}
            (source / "FREEZE.json").write_text(json.dumps(freeze), encoding="utf-8")
            with patch.object(formal.subprocess, "run") as run:
                with self.assertRaisesRegex(SystemExit, "STOP_GITHUB_READBACK_NOT_VERIFIED"):
                    formal.run(source, out)
                run.assert_not_called()
            self.assertFalse((out / "FORMAL_STARTED.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
