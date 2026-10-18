import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def make_mutated_bundle(destination):
    target = destination / "source"
    shutil.copytree(SOURCE, target)
    workload_path = target / "workload.json"
    workload = json.loads(workload_path.read_text(encoding="utf-8"))
    dead_record = next(row for row in workload["records"] if row["id"] == "completed-note")
    dead_record["fields"]["text"] += " — changed after freeze"
    workload_bytes = (json.dumps(workload, ensure_ascii=False, indent=2) + "\n").encode()
    workload_path.write_bytes(workload_bytes)

    raw_path = target / "container-out" / "RAW.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["workload_sha256"] = sha256(workload_bytes)
    raw["canonical_record_sha256"]["completed-note"] = canonical_sha(dead_record)
    raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def run_auditor(script, evidence_root):
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "--root", str(evidence_root),
            "--raw", str(evidence_root / "container-out" / "RAW.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class FrozenWorkloadBindingTests(unittest.TestCase):
    def test_original_auditor_accepts_self_consistent_mutated_workload_control(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = make_mutated_bundle(Path(temp))
            result = subprocess.run(
                [
                    sys.executable,
                    str(evidence / "audit_a01.py"),
                    "--raw", str(evidence / "container-out" / "RAW.json"),
                    "--out", str(Path(temp) / "legacy-audit.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + "\n" + result.stdout)
            self.assertTrue(json.loads((Path(temp) / "legacy-audit.json").read_text())["passed"])

    def test_new_auditor_passes_exact_retained_source_bundle(self):
        result = run_auditor(ROOT / "audit_v2.py", SOURCE)
        self.assertEqual(result.returncode, 0, result.stderr)
        audit = json.loads(result.stdout)
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["classification"], "PASS_RETAINED_BYTES_SCOPED")

    def test_new_auditor_rejects_changed_workload_even_when_raw_is_self_consistent(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = make_mutated_bundle(Path(temp))
            result = run_auditor(ROOT / "audit_v2.py", evidence)
            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads(result.stdout)
            self.assertFalse(audit["passed"])
            self.assertEqual(audit["classification"], "FAIL_FREEZE_BINDING")
            self.assertFalse(audit["checks"]["workload_matches_prerun_sha256"])


if __name__ == "__main__":
    unittest.main()
