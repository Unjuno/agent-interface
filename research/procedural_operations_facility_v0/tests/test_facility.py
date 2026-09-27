#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "facility"
SEEDS = [int(x) for x in (ROOT / "seeds" / "regression.txt").read_text().split()]


def run(*args: str, input_text: str | None = None, check: bool = True):
    return subprocess.run(
        [str(BIN), *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
        cwd=ROOT,
    )


class FacilityTest(unittest.TestCase):
    def test_core_binary(self):
        cp = subprocess.run([str(ROOT / "build" / "test_core")], text=True, capture_output=True, check=True)
        self.assertIn("CORE_TEST_PASS", cp.stdout)

    def test_spec_is_seed_deterministic(self):
        a = json.loads(run("--spec", "--seed", "424242", "--difficulty", "0.55").stdout)
        b = json.loads(run("--spec", "--seed", "424242", "--difficulty", "0.55").stdout)
        c = json.loads(run("--spec", "--seed", "424243", "--difficulty", "0.55").stdout)
        self.assertEqual(a, b)
        self.assertNotEqual(a["spec_hash"], c["spec_hash"])

    def test_fixed_seed_oracle_sweep(self):
        for d in (0.0, 0.5, 1.0):
            for seed in SEEDS:
                with self.subTest(difficulty=d, seed=seed):
                    obj = json.loads(run("--oracle-run", "--seed", str(seed), "--difficulty", str(d)).stdout)
                    self.assertTrue(obj["success"], obj)
                    self.assertEqual(obj["failure_reason"], "none")

    def test_snapshot_is_deterministic_for_fixed_seed(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = pathlib.Path(td) / "a.ppm"
            p2 = pathlib.Path(td) / "b.ppm"
            run("--oracle-run", "--seed", "30303", "--difficulty", "0.7", "--render-every", "1", "--snapshot", str(p1))
            run("--oracle-run", "--seed", "30303", "--difficulty", "0.7", "--render-every", "1", "--snapshot", str(p2))
            self.assertEqual(hashlib.sha256(p1.read_bytes()).hexdigest(), hashlib.sha256(p2.read_bytes()).hexdigest())
            self.assertGreater(len(p1.read_bytes()), 100_000)

    def test_public_protocol_does_not_reveal_private_episode(self):
        cp = run("--stdio", "--seed", "777777", "--difficulty", "0.4", input_text="PUBLIC\nQUIT\n")
        public = cp.stdout
        self.assertNotIn("777777", public)
        self.assertNotIn("spec_hash", public)
        self.assertNotIn("code", public)
        self.assertNotIn("terminal", public)
        for line in public.splitlines():
            if line.startswith("{"):
                self.assertEqual(set(json.loads(line)), {"schema", "tick", "done"})

    def test_axis_override_is_independent(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td) / "base.json"
            mod = pathlib.Path(td) / "mod.json"
            run("--oracle-run", "--seed", "80808", "--difficulty", "0.4", "--report", str(base))
            run("--oracle-run", "--seed", "80808", "--difficulty", "0.4", "--set", "watcher_count=7", "--report", str(mod))
            a = json.loads(base.read_text())["config"]
            b = json.loads(mod.read_text())["config"]
            changed = {k for k in a if a[k] != b[k]}
            self.assertEqual(changed, {"watcher_count"})

    def test_invalid_parameter_rejected(self):
        cp = run("--spec", "--seed", "1", "--set", "watcher_count=99", check=False)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("outside valid range", cp.stderr)

    def test_seeded_mechanics_performance_smoke(self):
        obj = json.loads(run("--bench", "--seed", "424242", "--episodes", "120", "--difficulty", "0.6").stdout)
        self.assertEqual(obj["pass"], obj["episodes"])
        self.assertGreater(obj["episodes_per_second"], 100.0)
        self.assertGreater(obj["render_fps"], 500.0)

    def test_paired_harness_uses_identical_fixed_episode_without_exposing_seed(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            seed_file = td / "seeds.txt"
            seed_file.write_text("13579\n")
            out = td / "paired"
            ctl = f"python3 {ROOT / 'controllers' / 'noop_controller.py'}"
            subprocess.run([
                "python3", str(ROOT / "paired_harness.py"),
                "--seeds", str(seed_file),
                "--difficulty", "0.5",
                "--set", "world_deadline_ticks=60",
                "--left", ctl, "--right", ctl,
                "--output", str(out), "--max-cycles", "80",
            ], cwd=ROOT, text=True, capture_output=True, check=True)
            obj = json.loads((out / "paired-summary.json").read_text())
            self.assertEqual(len(obj["pairs"]), 1)
            pair = obj["pairs"][0]
            self.assertEqual(pair["left"], pair["right"])
            self.assertEqual(pair["seed"], 13579)
            self.assertTrue((out / "pair-0000" / "left" / "frames" / "frame-000000.ppm").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
