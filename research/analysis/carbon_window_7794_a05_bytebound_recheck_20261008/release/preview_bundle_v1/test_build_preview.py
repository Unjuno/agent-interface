from __future__ import annotations
import importlib.util
import io
import json
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

        required = set(mod.REQUIRED_TRACKED) | set(mod.ROOT_RELEASE_FILES)
        required.update({
            "runtime/helper.py",
            "release/helper.md",
            "research/live_control/runtime_dependency.py",
            "research/live_control/unrelated_asset.json",
            "research/doom/huge-raw.bin",
        })
        prereg_sources = {
            "runtime_dependency.py": "0" * 64,
            "source_from_prereg.py": "1" * 64,
        }
        required.add("research/live_control/source_from_prereg.py")
        for name in sorted(required):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == mod.RETAINED_FILES[0]:
                path.write_text(json.dumps({"sources": prereg_sources}) + "\n")
            elif name.endswith(".sh"):
                path.write_text("#!/usr/bin/env bash\necho ok\n")
                path.chmod(0o755)
            elif name.endswith("requirements-golden.txt"):
                path.write_text("example==1.0\n")
            elif name.endswith(".py"):
                path.write_text("VALUE = 1\n")
            elif name.endswith(".bin"):
                path.write_bytes(b"x" * 1024)
            else:
                path.write_text("{}\n")

        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"], check=True)
        return prereg_sources

    def test_selection_includes_runtime_release_python_and_prereg_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            selected = mod.select_release_paths(root, mod.tracked_files(root))
            self.assertIn("runtime/helper.py", selected)
            self.assertIn("release/helper.md", selected)
            self.assertIn("research/live_control/runtime_dependency.py", selected)
            self.assertIn("research/live_control/source_from_prereg.py", selected)
            self.assertNotIn("research/live_control/unrelated_asset.json", selected)
            self.assertNotIn("research/doom/huge-raw.bin", selected)

    def test_archive_is_deterministic_and_exact_selected_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            selected = mod.select_release_paths(root, mod.tracked_files(root))
            prefix = "preview-test"
            first = mod.deterministic_archive(root, prefix, selected)
            second = mod.deterministic_archive(root, prefix, selected)
            self.assertEqual(first, second)
            check = mod.verify_archive_bytes(first, prefix, selected)
            self.assertTrue(check["selected_closure_exact"])
            with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as tf:
                names = set(tf.getnames())
                self.assertNotIn(prefix + "/research/doom/huge-raw.bin", names)
                member = tf.getmember(prefix + "/runtime/golden-demo-v3.sh")
                self.assertTrue(member.mode & stat.S_IXUSR)

    def test_inspect_rejects_dirty_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            (root / "untracked-secret.txt").write_text("must-not-ship\n")
            with self.assertRaises(mod.BuildError):
                mod.inspect_rc(root)
            (root / "untracked-secret.txt").unlink()
            meta = mod.inspect_rc(root)
            self.assertEqual(len(meta["head"]), 40)
            self.assertLess(meta["selected_file_count"], meta["tracked_file_count"])

    def test_retained_source_names_must_be_flat_and_hashed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            prereg = root / mod.RETAINED_FILES[0]
            prereg.write_text(json.dumps({"sources": {"../escape.py": "0" * 64}}))
            with self.assertRaises(mod.BuildError):
                mod.retained_source_paths(root)


if __name__ == "__main__":
    unittest.main()
