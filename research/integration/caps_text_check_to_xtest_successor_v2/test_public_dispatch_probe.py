"""Real public-dispatch construction tests for the query-to-XTEST boundary."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
STUDY = Path(__file__).resolve().parent
PROBE = STUDY / "public_dispatch_probe.py"


class PublicDispatchProbeTest(unittest.TestCase):
    def run_arm(self, arm: str, out: Path) -> dict:
        command = [
            "xvfb-run", "-a", "-s", "-screen 0 640x240x24 -nolisten tcp",
            sys.executable, "-B", str(PROBE), "--repo", str(ROOT), "--out", str(out),
            "--arm", arm,
        ]
        result = subprocess.run(command, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout.splitlines()[-1])
        return json.loads(Path(summary["record"]).read_text(encoding="utf-8"))

    def test_public_dispatch_guard_race_and_controls(self):
        with tempfile.TemporaryDirectory(prefix="public-dispatch-caps-") as tmp:
            root = Path(tmp)
            current = self.run_arm("current", root / "current")
            stable = self.run_arm("guard-stable", root / "guard-stable")
            raced = self.run_arm("guard-interposed", root / "guard-interposed")

        self.assertEqual(current["app_after"]["value"], "aB2")
        self.assertEqual(stable["app_after"]["value"], "aB2")
        self.assertEqual(raced["app_after"]["value"], "Ab2")
        self.assertEqual(raced["before"]["lockmask"], 0)
        self.assertEqual(raced["actor"]["exit"], 0)
        actor = json.loads(raced["actor"]["stdout"])
        self.assertEqual(actor["candidate_sample"], 0)
        self.assertEqual(actor["post_lock"], 1)
        first_key = next(e for e in raced["entry_events"] if e["event"] == "KeyPress")
        self.assertLess(actor["ack_ns"], first_key["ns"])
        self.assertEqual(raced["after"]["lockmask"], 1)
        self.assertEqual(raced["after"]["keymap"], [0] * 32)
        self.assertIn("runtime.cli_v1.api", raced["runtime_imports"])
        self.assertIn("runtime.backends.x11_v1.backend", raced["runtime_imports"])
        self.assertNotEqual(stable["candidate_backend_sha256"], stable["main_backend_sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
