from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.distribution_v1.build import _source_bytes, build


class DistributionTests(unittest.TestCase):
    def test_build_is_byte_deterministic_and_runnable(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = td / "a.pyz"; b = td / "b.pyz"
            ma = td / "a.json"; mb = td / "b.json"
            sa = td / "a.sum"; sb = td / "b.sum"
            ra = build(root, a, ma, sa)
            rb = build(root, b, mb, sb)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(ra["sha256"], rb["sha256"])
            out = subprocess.check_output([sys.executable, str(a)], text=True)
            doctor = json.loads(out)
            self.assertFalse(doctor["support_claim"])
            self.assertFalse(doctor["ready_for_side_effects"])
            self.assertEqual(doctor["native_probe"]["input_authority"], "none")
            self.assertEqual(doctor["native_probe"]["capture_authority"], "none")

    def test_git_checkout_reads_committed_bytes_not_worktree_newlines(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "core.autocrlf", "false"], check=True)
            path = root / "sample.py"
            committed = b"VALUE = 1\nVALUE = 2\n"
            path.write_bytes(committed)
            subprocess.run(["git", "-C", str(root), "add", "sample.py"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"], check=True)
            path.write_bytes(committed.replace(b"\n", b"\r\n"))
            self.assertNotEqual(path.read_bytes(), committed)
            self.assertEqual(_source_bytes(root, "sample.py"), committed)

    def test_non_git_source_bytes_fall_back_to_filesystem(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "sample.py"
            data = b"VALUE = 1\r\n"
            path.write_bytes(data)
            self.assertEqual(_source_bytes(root, "sample.py"), data)


if __name__ == "__main__":
    unittest.main()
