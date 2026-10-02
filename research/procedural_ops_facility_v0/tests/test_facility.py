from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "facility"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(BIN), *args], cwd=ROOT, text=True, capture_output=True, check=check)


def report(seed: int, level: float = 0.45, *extra: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "report.json"
        cp = run("--headless", "--auto-reference", "--seed", str(seed), "--difficulty", str(level), "--report", str(p), *extra)
        assert cp.returncode == 0, cp.stderr
        return json.loads(p.read_text())


class FacilityTests(unittest.TestCase):
    def test_fixed_seed_replay_is_deterministic(self):
        a = report(424242, 0.45)
        b = report(424242, 0.45)
        for key in ("state_hash", "event_hash", "input_hash", "success", "ticks", "metrics"):
            self.assertEqual(a[key], b[key], key)

    def test_different_seed_changes_state_hash(self):
        a = report(424242, 0.45)
        b = report(424243, 0.45)
        self.assertNotEqual(a["state_hash"], b["state_hash"])

    def test_reference_controller_passes_fixed_seed_matrix(self):
        for level in (0.0, 0.35, 0.65, 1.0):
            for seed in (7, 19, 42, 314159, 424242):
                with self.subTest(level=level, seed=seed):
                    r = report(seed, level)
                    self.assertTrue(r["success"], r)
                    self.assertEqual(r["failure"], "none")
                    self.assertEqual(r["metrics"]["assembly_placed"], r["difficulty"]["assembly_pieces"])
                    self.assertEqual(r["metrics"]["recovery_events"], 1)
                    self.assertEqual(r["metrics"]["recovery_successes"], 1)

    def test_individual_difficulty_override_is_reported(self):
        r = report(42, 0.45, "--set", "watcher_count=6", "--set", "track_speed_px_per_tick=2.25")
        self.assertEqual(r["difficulty"]["watcher_count"], 6)
        self.assertAlmostEqual(r["difficulty"]["track_speed_px_per_tick"], 2.25)

    def test_invalid_override_fails_closed(self):
        cp = run("--headless", "--seed", "42", "--set", "watcher_count=99", check=False)
        self.assertNotEqual(cp.returncode, 0)

    def test_snapshot_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a.ppm"
            b = Path(td) / "b.ppm"
            run("--headless", "--auto-reference", "--seed", "424242", "--difficulty", "0.45", "--snapshot", str(a))
            run("--headless", "--auto-reference", "--seed", "424242", "--difficulty", "0.45", "--snapshot", str(b))
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertGreater(a.stat().st_size, 100_000)

    def test_mechanics_benchmark_runs(self):
        cp = run("--benchmark", "100", "--seed", "1000", "--difficulty", "0.45")
        data = json.loads(cp.stdout)
        self.assertEqual(data["passes"], 100)
        self.assertGreater(data["episodes_per_second"], 1.0)

    def test_render_benchmark_runs(self):
        cp = run("--render-benchmark", "60", "--seed", "424242")
        data = json.loads(cp.stdout)
        self.assertEqual(data["frames"], 60)
        self.assertGreater(data["frames_per_second"], 10.0)

    def test_fixed_suite_sweep_is_replayable(self):
        cmd = ["python3", str(ROOT / "sweep.py"), "--axis", "episode_deadline_ticks",
               "--values", "600,10800", "--difficulty", "0.45"]
        a = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
        b = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
        ja, jb = json.loads(a.stdout), json.loads(b.stdout)
        self.assertEqual(ja, jb)
        self.assertLess(ja["rows"][0]["success_rate"], ja["rows"][1]["success_rate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
