"""Re-run T2 in an isolated directory without mutating retained evidence."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class RunnerReplayTests(unittest.TestCase):
    def test_replay_matches_retained_result_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "replay"
            command = [sys.executable, "-B", str(ROOT / "run_t2.py"),
                       "--run-dir", str(run_dir)]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)

            audit = subprocess.run(
                [sys.executable, "-B", str(ROOT / "audit_t2.py"),
                 "--run-dir", str(run_dir)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("PASS_V15_PRODUCER_COMPOSITION_SCOPED", audit.stdout)

            for relative in ("candidate.json", "input-records.json",
                             "scorer/scorer-samples.jsonl",
                             "scorer/scorer-events.jsonl", "scorer/scorer-summary.json"):
                retained = json.loads((ROOT / "run" / relative).read_text(encoding="utf-8")) \
                    if relative.endswith(".json") else [
                        json.loads(line) for line in
                        (ROOT / "run" / relative).read_text(encoding="utf-8").splitlines()
                    ]
                replay = json.loads((run_dir / relative).read_text(encoding="utf-8")) \
                    if relative.endswith(".json") else [
                        json.loads(line) for line in
                        (run_dir / relative).read_text(encoding="utf-8").splitlines()
                    ]
                self.assertEqual(replay, retained, relative)

            snapshot = {path.relative_to(run_dir): path.read_bytes()
                        for path in run_dir.rglob("*") if path.is_file()}
            repeated = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("refusing to append or overwrite", repeated.stderr)
            self.assertEqual(snapshot, {path.relative_to(run_dir): path.read_bytes()
                                        for path in run_dir.rglob("*") if path.is_file()})


if __name__ == "__main__":
    unittest.main()
