import unittest
from unittest.mock import patch
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import runtime.golden_desktop_demo_v3 as demo


class GoldenDesktopV3DoctorTests(unittest.TestCase):
    def test_doctor_adds_the_runtime_modules_missing_from_v1(self):
        base = {"schema": "old", "passed": True,
                "checks": [{"name": "base", "passed": True, "detail": "ok"}]}
        fake = type("Module", (), {"__version__": "1.2.3"})()
        with patch.object(demo, "BASE_DOCTOR", return_value=base), \
             patch.object(demo.importlib, "import_module", return_value=fake) as imported:
            result = demo.doctor()
        self.assertTrue(result["passed"])
        self.assertEqual(result["schema"], "agent_interface_golden_doctor_v2")
        self.assertEqual([row["name"] for row in result["checks"][-2:]],
                         ["python:openpyxl", "python:et_xmlfile"])
        self.assertEqual(imported.call_count, 2)

    def test_missing_runtime_module_fails_doctor_before_model_work(self):
        base = {"schema": "old", "passed": True,
                "checks": [{"name": "base", "passed": True, "detail": "ok"}]}
        with patch.object(demo, "BASE_DOCTOR", return_value=base), \
             patch.object(demo.importlib, "import_module",
                          side_effect=ModuleNotFoundError("missing")):
            result = demo.doctor()
        self.assertFalse(result["passed"])
        self.assertTrue(all(not row["passed"] for row in result["checks"][-2:]))


class GoldenDesktopV3RetainedAuditTests(unittest.TestCase):
    base = demo.previous.base
    def make_packet(self, root: Path):
        research = root / "research" / "live_control"
        retained = research / "results" / "integrated-efficiency-live-01"
        archive = research / "results" / "integrated-efficiency-live-01-frozen-source-v1"
        retained.mkdir(parents=True)
        archive.mkdir(parents=True)
        source_bytes = b"FROZEN = True\n"
        digest = hashlib.sha256(source_bytes).hexdigest()
        plan = {"sources": {"frozen.py": digest}, "scope": "finite"}
        (retained / "preregistration.json").write_text(json.dumps(plan))
        evaluation = {"disposition": "RETAIN", "observed_break_even_task": 2,
                      "arms": {arm: {"correct": True, "cumulative_planner_generations": [1]}
                               for arm in ("plain", "ephemeral", "persistent")}}
        (retained / "report.json").write_text(json.dumps({"evaluation": evaluation}))
        (retained / "audit.json").write_text(json.dumps({"passed": True, "exact_tasks": {},
                                                          "final_input_tokens": {}, "elapsed_ms": {}}))
        archive_file = "frozen.py.source"
        (archive / archive_file).write_bytes(source_bytes)
        manifest = {
            "schema": "integrated_efficiency_live_frozen_source_archive_v1",
            "study": "integrated-efficiency-live-01", "source_commit": "a" * 40,
            "source_count": 1,
            "files": [{"name": "frozen.py", "archive_file": archive_file,
                       "source_path": "research/live_control/frozen.py", "sha256": digest,
                       "size_bytes": len(source_bytes)}],
        }
        (archive / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest))
        # Deliberately changed current source proves audit authority comes from
        # the byte-verified archive while drift remains visible in the result.
        (research / "frozen.py").write_text("CURRENT = True\n")
        return retained, archive, research

    def test_retained_audit_accepts_exact_archive_and_reports_current_drift(self):
        with TemporaryDirectory() as temp:
            retained, archive, research = self.make_packet(Path(temp))
            with patch.object(self.base, "RETAINED", retained), \
                 patch.object(self.base, "RETAINED_SOURCE_ARCHIVE", archive), \
                 patch.object(self.base, "RESEARCH", research):
                result = self.base.audit_retained()
        self.assertTrue(result["passed"])
        self.assertEqual(result["source_mismatches"], [])
        self.assertEqual(result["current_source_mismatches"], ["frozen.py"])
        self.assertEqual(result["source_validation"], "frozen_archive")

    def test_retained_audit_fails_if_frozen_archive_bytes_change(self):
        with TemporaryDirectory() as temp:
            retained, archive, research = self.make_packet(Path(temp))
            (archive / "frozen.py.source").write_bytes(b"changed\n")
            with patch.object(self.base, "RETAINED", retained), \
                 patch.object(self.base, "RETAINED_SOURCE_ARCHIVE", archive), \
                 patch.object(self.base, "RESEARCH", research):
                result = self.base.audit_retained()
        self.assertFalse(result["passed"])
        self.assertEqual(result["source_mismatches"], ["frozen.py"])


if __name__ == "__main__":
    unittest.main()
