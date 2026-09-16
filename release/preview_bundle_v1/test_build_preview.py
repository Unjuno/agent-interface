from __future__ import annotations
import gzip
import importlib.util
import io
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_preview", HERE / "build_preview.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)

class ArchiveTests(unittest.TestCase):
    def make_repo(self, root: Path):
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        for name in mod.REQUIRED_TRACKED:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name.endswith(".sh"):
                path.write_text("#!/usr/bin/env bash\necho ok\n")
                path.chmod(0o755)
            elif name.endswith("requirements-golden.txt"):
                path.write_text("example==1.0\n")
            elif name.endswith("preflight.py"):
                path.write_text("print('stub')\n")
            elif name.endswith(".py"):
                path.write_text("VALUE = 1\n")
            else:
                path.write_text("{}\n")
        (root / "tracked.txt").write_text("tracked\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"], check=True)
        (root / "untracked-secret.txt").write_text("must-not-ship\n")

    def test_archive_is_deterministic_and_tracked_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            prefix = "preview-test"
            first = mod.deterministic_archive(root, prefix)
            second = mod.deterministic_archive(root, prefix)
            self.assertEqual(first, second)
            with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as tf:
                names = set(tf.getnames())
                self.assertIn(prefix + "/tracked.txt", names)
                self.assertNotIn(prefix + "/untracked-secret.txt", names)
                member = tf.getmember(prefix + "/runtime/golden-demo-v3.sh")
                self.assertTrue(member.mode & stat.S_IXUSR)

    def test_required_closure_and_mode_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            prefix = "preview-test"
            archive = mod.deterministic_archive(root, prefix)
            check = mod.verify_archive_bytes(archive, prefix)
            self.assertTrue(check["required_files_present"])
            self.assertTrue(check["launcher_modes_preserved"])

    def test_inspect_rejects_dirty_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            with self.assertRaises(mod.BuildError):
                mod.inspect_rc(root)
            (root / "untracked-secret.txt").unlink()
            meta = mod.inspect_rc(root)
            self.assertEqual(len(meta["head"]), 40)

if __name__ == "__main__":
    unittest.main()
