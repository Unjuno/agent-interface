"""Regression and mutation tests for the offline WSLc smoke receipt auditor."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
AUDITOR = ROOT / "audit_t0.py"


class SmokeReceiptAuditTests(unittest.TestCase):
    def run_audit(self, evidence: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(AUDITOR), "--root", str(evidence)],
            capture_output=True, text=True, check=False,
        )

    def copy_evidence(self, destination: Path) -> Path:
        target = destination / "evidence"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("test_audit_t0.py", "__pycache__"))
        return target

    def test_auditor_accepts_the_retained_one_shot_receipt(self) -> None:
        completed = self.run_audit(ROOT)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS_T0_RECEIPT_AUDITED")
        self.assertEqual(result["wslc_builds"], 1)
        self.assertEqual(result["wslc_runs"], 1)
        self.assertEqual(result["retries"], 0)

    def test_auditor_rejects_a_changed_payload_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.copy_evidence(Path(temporary))
            output = evidence / "run.output.txt"
            warning, line = output.read_text(encoding="utf-8").splitlines()
            receipt = json.loads(line)
            receipt["payload_sha256"] = "0" * 64
            output.write_text(warning + "\n" + json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            completed = self.run_audit(evidence)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "STOP_T0_RECEIPT_INVALID")

    def test_auditor_rejects_a_surviving_named_container(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.copy_evidence(Path(temporary))
            state = json.loads((evidence / "POSTRUN_CHECK.json").read_text(encoding="utf-8"))
            state["target_container_present_after_run"] = True
            (evidence / "POSTRUN_CHECK.json").write_text(json.dumps(state), encoding="utf-8")
            completed = self.run_audit(evidence)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "STOP_T0_RECEIPT_INVALID")

    def test_auditor_rejects_mutated_frozen_probe_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.copy_evidence(Path(temporary))
            with (evidence / "probe.py").open("ab") as stream:
                stream.write(b"# mutation\n")
            completed = self.run_audit(evidence)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "STOP_T0_RECEIPT_INVALID")

    def test_auditor_rejects_build_output_without_cached_base_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.copy_evidence(Path(temporary))
            output = evidence / "build.output.txt"
            output.write_text(output.read_text(encoding="utf-8").replace("[1/4] CACHED\n", ""), encoding="utf-8")
            completed = self.run_audit(evidence)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "STOP_T0_RECEIPT_INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
