from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from runtime.distribution_v2.build import FIXED_TIME, GENERATED, SOURCE_FILES, SUPPORT, build


class PortableDistributionTests(unittest.TestCase):
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
