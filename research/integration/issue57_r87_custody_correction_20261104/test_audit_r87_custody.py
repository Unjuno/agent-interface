import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("audit_r87_custody.py")
BASE = "research/integration/issue57_calc_sameframe_live_20261103_r87/r87-c11/"


class CustodyAuditTests(unittest.TestCase):
    def run_audit(self, revision):
        env = dict(os.environ)
        env.pop("GIT_DIR", None)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), revision],
            cwd=SCRIPT.parents[3], env=env, text=True, capture_output=True,
        )
        return completed.returncode, json.loads(completed.stdout)

    def test_complete_and_mismatch_trees_are_distinguished(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "audit@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Audit Test"], check=True)
            packet = repo / BASE
            packet.mkdir(parents=True)
            payload = b"actual bytes\n"
            (packet / "a.bin").write_bytes(payload)
            manifest = {
                "files": [{"path": "a.bin", "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}]
            }
            (packet / "SHA256SUMS.json").write_text(json.dumps(manifest), encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "verified"], check=True)
            good, report = self.run_audit(f"--git-dir={repo / '.git'}") if False else (None, None)
            # Run the script with a test-only GIT_DIR override for its git subprocesses.
            env = dict(os.environ, GIT_DIR=str(repo / ".git"))
            env.pop("GIT_WORK_TREE", None)
            ok = subprocess.run([sys.executable, str(SCRIPT), "HEAD"], cwd=SCRIPT.parents[3], env=env, text=True, capture_output=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            ok_report = json.loads(ok.stdout)
            self.assertEqual((ok_report["verified"], ok_report["missing"], ok_report["mismatched"]), (1, [], []))
            self.assertEqual(ok_report["tracked_packet_files"], 2)

            (packet / "a.bin").write_bytes(b"changed\n")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "mismatch"], check=True)
            bad = subprocess.run([sys.executable, str(SCRIPT), "HEAD"], cwd=SCRIPT.parents[3], env=env, text=True, capture_output=True)
            self.assertEqual(bad.returncode, 1, bad.stderr)
            bad_report = json.loads(bad.stdout)
            self.assertEqual(bad_report["status"], "custody_mismatch")
            self.assertEqual([item["path"] for item in bad_report["mismatched"]], ["a.bin"])

    def test_packet_absent_is_distinguished(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "README").write_text("empty", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Audit", "-c", "user.email=audit@example.invalid", "commit", "-qm", "empty"], check=True)
            env = dict(os.environ, GIT_DIR=str(repo / ".git"))
            env.pop("GIT_WORK_TREE", None)
            result = subprocess.run([sys.executable, str(SCRIPT), "HEAD"], cwd=SCRIPT.parents[3], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "packet_absent")


if __name__ == "__main__":
    unittest.main()
