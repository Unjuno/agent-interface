import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import audit
import probe


class ProbeConstructionTests(unittest.TestCase):
    def test_output_collision_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "already-there"
            path.mkdir()
            result = subprocess.run([sys.executable, "probe.py", str(path)],
                                    capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(path.is_dir())
            self.assertEqual(list(path.iterdir()), [])

    def test_child_timeout_diagnostic_is_preserved(self):
        result = probe.bounded_run([sys.executable, "-c",
                                    "import time; print('READY-WAIT',flush=True); time.sleep(5)"], 0.15)
        self.assertTrue(result["timeout"])
        self.assertIn("READY-WAIT", result["output"])
        self.assertEqual(result["exit_code"], 124)

    def test_valid_shape_audits(self):
        sample = {
            "schema": "issue5243-private-xvfb-host-wrapper-v1", "timeout": False,
            "exit_code": 0, "host_socket_unchanged": True,
            "host_socket_before": {"mode": 511, "inode": 2, "device": 84},
            "host_socket_after": {"mode": 511, "inode": 2, "device": 84},
            "child": {"schema": "issue5243-private-xvfb-construction-v1",
                      "namespace_private": True, "child_mount_ns_inode": 8,
                      "host_mount_ns_inode": 7,
                      "socket_mount": {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": "tmpfs"},
                      "socket_dir_mode": 0o1777, "xvfb_ready": True,
                      "display": ":97", "screen": [640, 480],
                      "x_socket_exists": True, "xvfb_exit_code": 0}}
        self.assertEqual(audit.audit(sample)["status"], "PASS_PRIVATE_XVFB_CONSTRUCTION_ONLY")
        rejected = audit.mutation_controls(sample)
        self.assertEqual(len(rejected), 5)

    def test_incomplete_evidence_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            audit.audit({"schema": "issue5243-private-xvfb-host-wrapper-v1"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
