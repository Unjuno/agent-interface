"""Behavioral tests for preserving the original A01 archive during audit."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
ARCHIVE = REPO / "research/doom/v39_application_consumption_conflict_59_a01_20261005"
OLD_AUDITOR = ARCHIVE / "audit_a01.py"
NEW_AUDITOR = PACKAGE / "audit_readonly_v2.py"


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file() and
        "__pycache__" not in path.parts
    }


class ReadOnlyArchiveAuditTests(unittest.TestCase):
    def clone_archive(self, root):
        target = root / "archive"
        shutil.copytree(ARCHIVE, target)
        return target

    def test_v1_auditor_writes_into_the_hashed_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            clone = self.clone_archive(Path(temporary))
            before = snapshot(clone)
            # Use exec so the write interceptor observes behavior without relying
            # on filesystem timestamp resolution or platform newline conversion.
            code = "\n".join([
                "import json, runpy, sys",
                "from pathlib import Path",
                "script = Path(sys.argv[1])",
                "writes = []",
                "original = Path.write_text",
                "def spy(self, *args, **kwargs):",
                "    writes.append(self.relative_to(script.parent).as_posix())",
                "    return original(self, *args, **kwargs)",
                "Path.write_text = spy",
                "sys.argv = [str(script)]",
                "try:",
                "    runpy.run_path(str(script), run_name='__main__')",
                "except SystemExit as result:",
                "    code = result.code",
                "print(json.dumps({'write_targets': writes, 'exit_code': code}))",
            ])
            completed = subprocess.run(
                [sys.executable, "-B", "-c", code, str(clone / "audit_a01.py")],
                cwd=clone, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            observed = json.loads(completed.stdout.splitlines()[-1])
            self.assertEqual(observed["exit_code"], 0)
            self.assertEqual(observed["write_targets"], ["raw/AUDIT.json"])
            after = snapshot(clone)
            self.assertEqual(set(before), set(after))
            self.assertEqual(set(before) - {"raw/AUDIT.json"},
                             {name for name in before if before[name] == after[name]})
            self.assertNotEqual(before["raw/AUDIT.json"], after["raw/AUDIT.json"])

    def test_readonly_v2_passes_without_changing_any_archive_byte(self):
        with tempfile.TemporaryDirectory() as temporary:
            clone = self.clone_archive(Path(temporary))
            before = snapshot(clone)
            completed = subprocess.run(
                [sys.executable, "-B", str(NEW_AUDITOR), "--archive", str(clone)],
                cwd=REPO, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "PASS_READ_ONLY_ARCHIVE_AUDIT")
            self.assertEqual(result["baseline_false_accept_count"], 4)
            self.assertEqual(result["candidate_false_accept_count"], 0)
            self.assertEqual(result["interval_sweep"]["baseline"],
                             {"cases": 100, "ordered": 15, "incomplete": 85})
            self.assertEqual(result["interval_sweep"]["candidate"],
                             {"cases": 100, "ordered": 15, "incomplete": 85})
            self.assertEqual(snapshot(clone), before)

    def test_readonly_v2_detects_tampering_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            clone = self.clone_archive(Path(temporary))
            target = clone / "raw/A01.json"
            tampered = json.loads(target.read_text(encoding="utf-8"))
            tampered["candidate_false_accept_count"] = 1
            target.write_text(json.dumps(tampered), encoding="utf-8")
            before = snapshot(clone)
            completed = subprocess.run(
                [sys.executable, "-B", str(NEW_AUDITOR), "--archive", str(clone)],
                cwd=REPO, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "FAIL_READ_ONLY_ARCHIVE_AUDIT")
            self.assertTrue(result["errors"])
            self.assertEqual(snapshot(clone), before)


if __name__ == "__main__":
    unittest.main()
