"""Construction-only tests. These do not start Docker or train a model."""
import tempfile
import unittest
from pathlib import Path
import formal
import audit_v3


class FormalArgvTests(unittest.TestCase):
    def test_builder_binds_exact_seed_and_output_and_is_offline_readonly(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seed = formal.SEEDS[0]
            out = root / f"seed-{seed}" / "builder"
            out.mkdir(parents=True)
            cmd = formal.builder_argv(seed, out, root, b"print('frozen')", formal.IMAGE_ID)
            self.assertIn(f"NEEDLE_SEED={seed}", cmd)
            self.assertIn("NEEDLE_OUTPUT=/out", cmd)
            self.assertIn("--network", cmd)
            self.assertEqual(cmd[cmd.index("--network") + 1], "none")
            self.assertIn("--read-only", cmd)
            self.assertIn("--cpus=1", cmd)
            self.assertIn("--memory=2g", cmd)
            self.assertIn("--pids-limit=64", cmd)
            self.assertIn(f"{root.resolve()}:/src:ro", cmd)
            self.assertIn(f"{out.resolve()}:/out:rw", cmd)

    def test_missing_or_invalid_seed_stops_before_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for seed in (None, 0, formal.SEEDS[0] + 1):
                with self.assertRaises(formal.Stop):
                    formal.validate_output(seed, root)
        for seed_env, output_env in ((None, "/out"), ("bad", "/out"), (str(formal.SEEDS[0]), None),
                                     (str(formal.SEEDS[0]), "/wrong")):
            with self.assertRaises(formal.Stop):
                formal.validate_bindings(seed_env, output_env)

    def test_seed_offsets_are_disjoint_inside_fresh_block(self):
        spans = [set(range(seed + 1, seed + 13)) for seed in formal.SEEDS]
        for i, left in enumerate(spans):
            for right in spans[i + 1:]:
                self.assertTrue(left.isdisjoint(right))

    def test_output_must_be_unique_empty_seed_builder_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seed = formal.SEEDS[0]
            right = root / f"seed-{seed}" / "builder"
            right.mkdir(parents=True)
            self.assertEqual(formal.validate_output(seed, right), right.resolve())
            (right / "occupied").write_text("x")
            with self.assertRaisesRegex(formal.Stop, "NOT_EMPTY"):
                formal.validate_output(seed, right)
            with self.assertRaises(formal.Stop):
                formal.validate_output(seed, root / "builder")

    def test_loader_has_separate_readonly_package_and_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "skill.json"
            expected = root / "expected.json"
            package.write_text("{}")
            expected.write_text("{}")
            out = root / "seed-1" / "load1"
            out.mkdir(parents=True)
            cmd = formal.loader_argv(root, b"pass", package, expected, out, formal.IMAGE_ID)
            self.assertIn(f"{package.resolve()}:/package/skill.json:ro", cmd)
            self.assertIn(f"{expected.resolve()}:/expected.json:ro", cmd)
            self.assertIn("--network", cmd)
            self.assertIn("--read-only", cmd)

    def test_accuracy_recomputation_rejects_wrong_or_missing_rows(self):
        gold = [i % 4 for i in range(4096)]
        self.assertEqual(audit_v3.accuracy(gold, gold), 1.0)
        wrong = list(gold)
        wrong[0] = (wrong[0] + 1) % 4
        self.assertLess(audit_v3.accuracy(wrong, gold), 1.0)
        with self.assertRaises(ValueError):
            audit_v3.accuracy([], gold)


if __name__ == "__main__":
    unittest.main()
