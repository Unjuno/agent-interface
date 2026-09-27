import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import CASES, expected_case_names, wait_until_started

from work.issue5074.construction.protocol import CASES, expected_case_names


class MarkerProbeTest(unittest.TestCase):
    def test_frozen_case_matrix_has_seven_unique_cases(self):
        names = expected_case_names()
        self.assertEqual(len(names), 7)
        self.assertEqual(len(set(names)), 7)
        self.assertEqual(names[2], "timeout-after-start")
        self.assertEqual(CASES[2]["child_sleep"], 5)
        self.assertEqual(CASES[2]["broker_timeout"], 2)

    def test_parent_observes_started_child_before_deadline(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            marker = root / "started"
            child = root / "child.py"
            child.write_text(
                "import pathlib,sys,time\n"
                "pathlib.Path(sys.argv[1]).write_text('started')\n"
                "time.sleep(3)\n",
                encoding="utf-8",
            )
            proc = subprocess.Popen([sys.executable, str(child), str(marker)])
            deadline = time.monotonic() + 2
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "started")
            proc.kill()
            proc.wait(timeout=2)

    def test_protocol_refuses_missing_marker(self):
        class Exited:
            def poll(self):
                return 0
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError, "exited before"):
                wait_until_started(Path(td) / "missing", Exited(), 0.1)


if __name__ == "__main__":
    unittest.main()
