"""Focused artifact tests; no backend, GUI, model or native input is invoked."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from runtime.distribution_v2.build_validator import SOURCE_MAP, build

ROOT = Path(__file__).resolve().parents[2]


class ValidatorZipappTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        for src, _ in SOURCE_MAP:
            target = self.source / src
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / src, target)

    def make(self, name="validator"):
        out = self.base / (name + ".pyz")
        result = build(self.source, out, self.base / (name + ".json"),
                       self.base / (name + ".sha256"))
        return out, result

    def invoke(self, out, raw):
        case = self.base / "input.json"
        case.write_bytes(raw)
        env = {k: v for k, v in os.environ.items()
               if k not in ("PYTHONPATH", "DISPLAY", "WAYLAND_DISPLAY")}
        result = subprocess.run([sys.executable, "-I", "-S", str(out), "--program", str(case)],
                                cwd=self.base, env=env, capture_output=True, timeout=10)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(case.read_bytes(), raw)
        return result.returncode, json.loads(result.stdout)

    @staticmethod
    def program():
        return {"schema": "agent-interface/program-v1", "program_id": "construction",
                "source": {"observation_seq": 0, "binding_revision": 0},
                "authority": {"lease_id": "old", "expires_at_ns": 1},
                "terminal": {"release_all_required": True}, "ops": [{"op": "release_all"}]}

    def test_exact_source_and_inventory(self):
        out, result = self.make()
        with zipfile.ZipFile(out) as archive:
            self.assertEqual(set(archive.namelist()),
                             {dest for _, dest in SOURCE_MAP} | {"runtime/__init__.py", "BUILD.json"})
            for src, dest in SOURCE_MAP:
                self.assertEqual(archive.read(dest), (self.source / src).read_bytes())
        self.assertFalse(result["backend_included"])

    def test_deterministic(self):
        first, _ = self.make("one")
        second, _ = self.make("two")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_manifest(self):
        out, result = self.make()
        self.assertEqual(result["sha256"], hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(result["source_kind"], "directory_snapshot")
        self.assertIsNone(result["source_revision"])

    def test_valid_outside_checkout(self):
        out, _ = self.make()
        code, report = self.invoke(out, json.dumps(self.program()).encode())
        self.assertEqual(code, 0)
        self.assertTrue(report["static_valid"])
        self.assertFalse(report["side_effect_authority"])
        self.assertEqual(report["runtime_admission"], "not_evaluated")
        self.assertIsNone(report["task_success"])

    def test_invalid_shape(self):
        out, _ = self.make()
        code, report = self.invoke(out, b"[]")
        self.assertEqual((code, report["error"]), (1, "PROGRAM_NOT_OBJECT"))

    def test_invalid_json(self):
        out, _ = self.make()
        code, report = self.invoke(out, b"{")
        self.assertEqual((code, report["error"]), (2, "INVALID_JSON"))

    def test_existing_output_refused(self):
        self.make()
        with self.assertRaises(FileExistsError):
            self.make()

    def test_path_alias_refused(self):
        path = self.base / "one"
        with self.assertRaises(ValueError):
            build(self.source, path, path, self.base / "sum")

    def test_missing_source(self):
        (self.source / SOURCE_MAP[0][0]).unlink()
        with self.assertRaises(FileNotFoundError):
            self.make()
        self.assertFalse((self.base / "validator.pyz").exists())

    @unittest.skipUnless(shutil.which("git"), "git required for committed-source test")
    def test_committed_source_ignores_dirty_copy(self):
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.STDOUT)
        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=ArtifactTest", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "construction sources")
        first, metadata = self.make("one")
        self.assertEqual(metadata["source_kind"], "committed")
        (self.source / SOURCE_MAP[0][0]).write_text("dirty working copy\n")
        second, _ = self.make("two")
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
