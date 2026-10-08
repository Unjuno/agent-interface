import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

import audit
import probe


class ResetTerminateTests(unittest.TestCase):
    def test_bounded_timeout_retains_diagnostic_and_reaps_group(self):
        result = probe.bounded_run([sys.executable, "-c", "import time; print('READY-WAIT',flush=True); time.sleep(5)"], 0.15)
        self.assertTrue(result["timeout"])
        self.assertEqual(result["exit_code"], 124)
        self.assertIn("READY-WAIT", result["output"])

    def test_output_collision_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "exists"
            target.mkdir()
            result = subprocess.run([sys.executable, "-B", "probe.py", str(target)], capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(target.iterdir()), [])

    def test_mountinfo_source_tokens_are_explicitly_bounded(self):
        for source in ("none", "tmpfs"):
            m = {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": source}
            self.assertEqual(m["target"], "/tmp/.X11-unix")
            self.assertIn(m["source"], ("none", "tmpfs"))

    def test_auditor_and_six_corruption_controls(self):
        sample = {
            "schema": "issue5243-xvfb-reset-host-v1", "timeout": False, "exit_code": 0,
            "host_socket_unchanged": True,
            "host_mount_ns_inode": 8,
            "host_socket_before": {"mode": 511, "inode": 2, "device": 84},
            "host_socket_after": {"mode": 511, "inode": 2, "device": 84},
            "child": {
                "schema": "issue5243-xvfb-reset-child-v1", "namespace_private": True,
                "child_mount_ns_inode": 9, "host_mount_ns_inode": 8,
                "socket_mount": {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": "none"},
                "socket_dir_mode": 0o1777, "noreset_used": False,
                "xvfb_args": ["-terminate"], "xvfb_ready": True, "display": ":98",
                "screen": [640, 480], "x_socket_exists": True,
                "natural_exit": True, "xvfb_exit_code": 0
            }
        }
        self.assertEqual(audit.audit(sample)["status"], "PASS_PRIVATE_XVFB_RESET_TERMINATION_CONSTRUCTION_ONLY")
        self.assertEqual(len(audit.mutation_controls(sample)), 6)

    def test_incomplete_raw_is_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            audit.audit({"schema": "issue5243-xvfb-reset-host-v1"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
