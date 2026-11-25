from __future__ import annotations
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_preview", HERE / "build_preview.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class ArchiveTests(unittest.TestCase):
    gui_sources = {
        "research/observation_tiles/tile_transport.py",
        "research/observation_tiles/image_artifact.py",
        "research/observation_gating/gui_suite.py",
        "research/observation_gating/exact_gate.py",
        "research/real_apps_v1/real_app_suite_v1.py",
    }

    @unittest.skipUnless(shutil.which("sh"), "quickstart commands require a POSIX shell")
    def test_quickstart_enters_the_checksummed_archive_directory(self):
        guide = (HERE / "QUICKSTART.md").read_text(encoding="utf-8")
        instructions = guide.split("## Verify the download", 1)[1].split("## Static first-run check", 1)[0]
        commands = re.findall(r"^```bash\n(.*?)^```$", instructions, re.MULTILINE | re.DOTALL)
        self.assertTrue(commands)
        prefix = "agent-interface-research-preview-20260917+123456789abc"
        with tempfile.TemporaryDirectory() as td:
            downloads = Path(td)
            archive = downloads / (prefix + ".tar.gz")
            with tarfile.open(archive, "w:gz") as bundle:
                directory = tarfile.TarInfo(prefix)
                directory.type = tarfile.DIRTYPE
                directory.mode = 0o755
                bundle.addfile(directory)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            (downloads / "SHA256SUMS").write_bytes(f"{digest}  {archive.name}\n".encode())
            (downloads / "agent-interface-research-preview-older").mkdir()
            (downloads / "agent-interface-research-preview-older.tar.gz").touch()
            script = "\n".join(commands) + '\ntest "${PWD##*/}" = "$1"'
            completed = subprocess.run(
                ["sh", "-ec", script, "quickstart", prefix], cwd=downloads, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def make_repo(self, root: Path):
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)

        required = set(mod.REQUIRED_TRACKED) | set(mod.ROOT_RELEASE_FILES)
        required.update(self.gui_sources)
        required.add(".gitattributes")
        required.update({
            "runtime/helper.py",
            "release/helper.md",
            "research/live_control/runtime_dependency.py",
            "research/live_control/unrelated_asset.json",
            "research/observation_tiles/benchmark_image_artifact.py",
            "research/doom/huge-raw.bin",
        })
        source_bytes = b"VALUE = 1\n"
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        prereg_sources = {"runtime_dependency.py": source_digest,
                          "source_from_prereg.py": source_digest}
        required.add("research/live_control/source_from_prereg.py")
        archive_dir = "research/live_control/results/integrated-efficiency-live-01-frozen-source-v1"
        manifest_path = archive_dir + "/SOURCE_MANIFEST.json"
        required.add(manifest_path)
        for name in prereg_sources:
            required.add(archive_dir + "/" + name + ".source")
        for name in sorted(required):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == ".gitattributes":
                path.write_text(
                    "/research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/** -text\n"
                )
            elif name == mod.RETAINED_FILES[0]:
                path.write_text(json.dumps({"sources": prereg_sources}) + "\n")
            elif name == manifest_path:
                files = [{"name": source, "archive_file": source + ".source",
                          "source_path": "research/live_control/" + source,
                          "sha256": digest, "size_bytes": len(source_bytes)}
                         for source, digest in prereg_sources.items()]
                path.write_text(json.dumps({
                    "schema": "integrated_efficiency_live_frozen_source_archive_v1",
                    "study": "integrated-efficiency-live-01", "source_commit": "a" * 40,
                    "source_count": len(files), "files": files,
                }) + "\n")
            elif path.name.endswith(".source"):
                path.write_bytes(source_bytes)
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
        for launcher in ("runtime/golden-demo-v3.sh", "runtime/setup-golden-demo-v3.sh"):
            subprocess.run(["git", "-C", str(root), "update-index", "--chmod=+x", launcher], check=True)
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
            self.assertIn(mod.RETAINED_SOURCE_MANIFEST, selected)
            self.assertIn(
                "research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/runtime_dependency.py.source",
                selected,
            )
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
                self.assertLessEqual({f"{prefix}/{name}" for name in self.gui_sources}, names)
                self.assertNotIn(prefix + "/research/observation_tiles/benchmark_image_artifact.py", names)
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

    def test_inspect_uses_bounded_stage_listing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            with patch.object(mod, "_git", wraps=mod._git) as git_call:
                meta = mod.inspect_rc(root)
            stage_calls = [call for call in git_call.call_args_list
                           if len(call.args) >= 3 and call.args[1:3] == ("ls-files", "--stage")]
            self.assertEqual(len(stage_calls), 1)
            self.assertEqual(stage_calls[0].args[3:], ("-z",))
            self.assertTrue(stage_calls[0].kwargs.get("binary"))
            self.assertGreater(meta["selected_file_count"], 0)

    def test_retained_source_names_must_be_flat_and_hashed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            prereg = root / mod.RETAINED_FILES[0]
            prereg.write_text(json.dumps({"sources": {"../escape.py": "0" * 64}}))
            with self.assertRaises(mod.BuildError):
                mod.retained_source_paths(root)

    def test_frozen_archive_must_match_preregistration_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"; root.mkdir()
            self.make_repo(root)
            archived = root / "research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/runtime_dependency.py.source"
            archived.write_bytes(b"tampered\n")
            with self.assertRaises(mod.BuildError):
                mod.retained_source_archive_paths(root)


if __name__ == "__main__":
    unittest.main()
