from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock
from pathlib import Path

from runtime.distribution_v2.build import FIXED_TIME, GENERATED, SOURCE_FILES, SUPPORT, build


class PortableDistributionTests(unittest.TestCase):
    def test_build_pins_source_even_when_head_moves_between_files(self):
        from runtime.distribution_v2 import build as builder
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT).decode().strip()
            git('init')
            for value in ('old', 'new'):
                for name in ('a.py', 'b.py'):
                    (root/name).write_text(value)
                git('add', 'a.py', 'b.py')
                git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', value)
                if value == 'old': old = git('rev-parse', 'HEAD')
            pinned = git('rev-parse', 'HEAD')
            original = builder._source_bytes
            def read(path, rel, revision):
                data = original(path, rel, revision)
                if rel == 'a.py':
                    git('update-ref', 'HEAD', old, pinned)
                return data
            with mock.patch.object(builder, 'SOURCE_FILES', ('a.py', 'b.py')), \
                 mock.patch.object(builder, '_source_bytes', side_effect=read):
                result = build(root, root/'out.pyz', root/'manifest.json', root/'sums')
            self.assertEqual(git('rev-parse', 'HEAD'), old)
            self.assertEqual(result['source_revision'], pinned)
            with zipfile.ZipFile(root/'out.pyz') as archive:
                self.assertEqual(archive.read('a.py'), b'new')
                self.assertEqual(archive.read('b.py'), b'new')
                self.assertEqual(json.loads(archive.read('BUILD.json'))['source_revision'], pinned)

    def test_missing_commit_does_not_fall_back_to_working_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'.git').mkdir()
            with self.assertRaises(RuntimeError):
                build(root, root/'out.pyz', root/'manifest.json', root/'sums')
            self.assertFalse((root/'out.pyz').exists())
            self.assertFalse((root/'manifest.json').exists())

    def test_build_is_byte_deterministic_and_doctor_runs(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = td / "a.pyz"; b = td / "b.pyz"
            ma = td / "a.json"; mb = td / "b.json"
            sa = td / "a.sum"; sb = td / "b.sum"
            ra = build(root, a, ma, sa); rb = build(root, b, mb, sb)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(ra["sha256"], rb["sha256"])
            proc = subprocess.run([sys.executable, str(a), "doctor"], capture_output=True, text=True, check=True)
            rows = proc.stdout.strip().splitlines()
            self.assertEqual(len(rows), 1)
            doctor = json.loads(rows[0])
            self.assertEqual(doctor["schema"], "agent-interface/runtime-doctor-v1")
            self.assertFalse(doctor["side_effect_authority"])

    def test_archive_closure_has_only_promoted_executable_modules(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); out = td / "runtime.pyz"
            result = build(root, out, td / "manifest.json", td / "sum")
            expected = sorted(list(SOURCE_FILES) + list(GENERATED) + ["SUPPORT.json", "BUILD.json"])
            self.assertEqual(result["entries"], expected)
            with zipfile.ZipFile(out) as archive:
                self.assertEqual(archive.namelist(), expected)
                for info in archive.infolist():
                    self.assertEqual(info.date_time, FIXED_TIME)
                support = json.loads(archive.read("SUPPORT.json"))
                self.assertEqual(support, SUPPORT)
                self.assertFalse(support["wayland"]["promoted"])
            self.assertFalse(any("test" in name.lower() or "fixture" in name.lower() or "research" in name.lower() for name in expected))

    def test_malformed_targets_fail_before_native_backend(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); out = td / "runtime.pyz"
            build(root, out, td / "manifest.json", td / "sum")
            program = td / "program.json"; program.write_text("{}", encoding="utf-8")
            targets = td / "targets.json"; targets.write_text("{}", encoding="utf-8")
            proc = subprocess.run([
                sys.executable, str(out), "dispatch", "--program", str(program), "--targets", str(targets),
                "--current-observation-seq", "0", "--current-binding-revision", "0",
            ], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            row = json.loads(proc.stdout)
            self.assertEqual(row["status"], "backend_unavailable")
            observation = subprocess.run([
                sys.executable, str(out), "observe", "--targets", str(targets),
                "--target", "fixture", "--frame", "window_client", "--region", "0", "0", "10", "10",
            ], capture_output=True, text=True)
            self.assertNotEqual(observation.returncode, 0)
            self.assertEqual(json.loads(observation.stdout)["status"], "backend_unavailable")


if __name__ == "__main__":
    unittest.main()
