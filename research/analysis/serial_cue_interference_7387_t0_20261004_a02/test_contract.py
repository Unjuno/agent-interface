#!/usr/bin/env python3
"""A02 construction tests; no formal candidate or auditor invocation."""
import pathlib
import sys
import tempfile
import unittest
import importlib.util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "serial_cue_interference_7387_t0_20261004"))
import auditor
spec = importlib.util.spec_from_file_location("candidate_a02", HERE / "candidate.py")
candidate_a02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_a02)


class A02Contract(unittest.TestCase):
    def test_existing_empty_mount_root(self):
        with tempfile.TemporaryDirectory() as root:
            out = pathlib.Path(root) / "out"
            out.mkdir()
            candidate_a02.build(out)
            report = auditor.audit_package(out)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["presentation_rows"], 288)

    def test_nonempty_output_refused(self):
        with tempfile.TemporaryDirectory() as root:
            out = pathlib.Path(root) / "out"
            out.mkdir()
            sentinel = out / "owned.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError): candidate_a02.build(out)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_absent_output_root(self):
        with tempfile.TemporaryDirectory() as root:
            out = pathlib.Path(root) / "new-out"
            candidate_a02.build(out)
            self.assertTrue(auditor.audit_package(out)["ok"])


if __name__ == "__main__": unittest.main(verbosity=2)
