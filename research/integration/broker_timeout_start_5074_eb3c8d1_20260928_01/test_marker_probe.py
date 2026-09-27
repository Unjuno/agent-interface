import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import CASES, expected_case_names, wait_until_started
from runner import timeout_evidence_fields


class MarkerProbeTest(unittest.TestCase):
    def test_frozen_case_matrix_has_seven_unique_cases(self):
        names = expected_case_names()
        self.assertEqual(len(names), 7)
        self.assertEqual(len(set(names)), 7)
        self.assertEqual(names[2], "timeout-after-start")
        self.assertEqual(CASES[2]["child_sleep"], 8)
        self.assertEqual(CASES[2]["broker_timeout"], 5)

    def test_parent_observes_started_child_before_deadline(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            marker = root / "started"
            child = root / "child.py"
            child.write_text(
                "import json,pathlib,sys,time\n"
                "log=pathlib.Path(sys.argv[2])\n"
                "with log.open('w',encoding='utf-8') as f:\n"
                " f.write(json.dumps({'event':'child_started'})+'\\n'); f.flush()\n"
                "pathlib.Path(sys.argv[1]).write_text('started\\n')\n"
                "time.sleep(3)\n",
                encoding="utf-8",
            )
            proc = subprocess.Popen([sys.executable, str(child), str(marker),
                                     str(root / "call.jsonl")])
            deadline = time.monotonic() + 2
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.005)
            try:
                observed_ns, record = wait_until_started(
                    marker, root / "call.jsonl", proc)
                self.assertGreater(observed_ns, 0)
                self.assertEqual(record["event"], "child_started")
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=2)

    def test_protocol_refuses_missing_marker(self):
        class Exited:
            def poll(self):
                return 0
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError, "exited before"):
                wait_until_started(Path(td) / "missing", Path(td) / "call.jsonl",
                                   Exited(), 0.1)

    def test_timeout_row_serialization_is_complete_without_ambient_state(self):
        record = {"event": "child_started", "started_ns": 100}
        row = timeout_evidence_fields(101, record, None, 5.0)
        self.assertEqual(row["child_start_marker_ns"], 101)
        self.assertEqual(row["child_start_record"], record)
        self.assertIsNone(row["marker_error"])
        self.assertEqual(row["broker_timeout_s"], 5.0)


if __name__ == "__main__":
    unittest.main()
