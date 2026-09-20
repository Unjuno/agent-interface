"""Portable, non-mutating checks for the retained transport auditor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.live_control.issue_3311_host_ipc_v1 import audit_orbstack_v1_transport as auditor
from research.live_control.issue_3311_host_ipc_v1.audit_orbstack_v1_transport import verify_raw_manifest


def _refresh_raw_manifest_for_test(root: Path) -> None:
    manifest = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"raw-sha256.json", "audit.json"}
    }
    (root / "raw-sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")


class RawManifestAuditTest(unittest.TestCase):
    def test_manifest_detects_tampering_without_rewriting_baseline(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-manifest-") as temp:
            root = Path(temp)
            captured = root / "ipc" / "container.stdout.txt"
            captured.parent.mkdir()
            captured.write_text("original evidence\n", encoding="utf-8")
            manifest = root / "raw-sha256.json"
            manifest.write_text(json.dumps({
                "ipc/container.stdout.txt": hashlib.sha256(captured.read_bytes()).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
            original_manifest = manifest.read_bytes()

            self.assertTrue(verify_raw_manifest(root))
            captured.write_text("tampered evidence\n", encoding="utf-8")
            self.assertFalse(verify_raw_manifest(root))
            self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_missing_or_malformed_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-manifest-") as temp:
            root = Path(temp)
            self.assertFalse(verify_raw_manifest(root))
            (root / "raw-sha256.json").write_text("not-json", encoding="utf-8")
            self.assertFalse(verify_raw_manifest(root))

    def test_report_output_cannot_mutate_evidence_root_or_manifest(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-audit-output-") as temp:
            root = Path(temp) / "evidence"
            root.mkdir()
            (root / "raw-sha256.json").write_text("{}\n", encoding="utf-8")
            raw_file = root / "capture.txt"
            raw_file.write_text("immutable\n", encoding="utf-8")
            original_manifest = (root / "raw-sha256.json").read_bytes()
            original_raw = raw_file.read_bytes()

            for output in (root / "report.json", root / "raw-sha256.json", raw_file):
                with self.subTest(output=output.name), patch.object(auditor, "audit", return_value={"disposition": "PASS_TEST"}), patch.object(
                    sys, "argv", ["audit", str(root), "--output", str(output)]
                ), patch("sys.stdout"):
                    self.assertEqual(auditor.main(), 2)

            self.assertEqual((root / "raw-sha256.json").read_bytes(), original_manifest)
            self.assertEqual(raw_file.read_bytes(), original_raw)
            self.assertFalse((root / "report.json").exists())

    def test_report_output_is_written_outside_evidence_root(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-audit-output-") as temp:
            root = Path(temp) / "evidence"
            root.mkdir()
            report = Path(temp) / "reports" / "audit.json"
            with patch.object(auditor, "audit", return_value={"disposition": "PASS_TEST"}), patch.object(
                sys, "argv", ["audit", str(root), "--output", str(report)]
            ), patch("sys.stdout"):
                self.assertEqual(auditor.main(), 0)
            self.assertEqual(json.loads(report.read_text()), {"disposition": "PASS_TEST"})


class RetainedEvidenceAuditTest(unittest.TestCase):
    def test_both_retained_transport_bundles_pass_independent_audit(self):
        root = Path(__file__).resolve().parent
        evidence = root / "evidence"
        names = ("20260920-v1-transport-audit-01", "20260920-v1-transport-audit-02",
                 "20260920-v1-transport-audit-03")
        for name in names:
            with self.subTest(bundle=name):
                report = auditor.audit(evidence / name)
                self.assertEqual(report["disposition"], "PASS_V1_SYNTHETIC_TRANSPORT_ONLY")
                self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_portable_sidecar_reports_match_current_auditor_checks(self):
        root = Path(__file__).resolve().parent
        names = ("20260920-v1-transport-audit-01", "20260920-v1-transport-audit-02",
                 "20260920-v1-transport-audit-03")
        for index, name in enumerate(names, start=1):
            with self.subTest(bundle=name):
                report = auditor.audit(root / "evidence" / name)
                sidecar = json.loads((root / "audit-reports" /
                                      f"20260920-portable-reaudit-0{index}.json").read_text())
                self.assertEqual(sidecar["disposition"], report["disposition"])
                self.assertEqual(sidecar["checks"], report["checks"])

    def test_audit_rejects_run_image_not_bound_to_inspected_image(self):
        source_root = Path(__file__).resolve().parent
        name = "20260920-v1-transport-audit-01"
        with tempfile.TemporaryDirectory(prefix="3311-v1-image-binding-") as temp:
            package = Path(temp) / source_root.name
            evidence = package / "evidence"
            evidence.mkdir(parents=True)
            shutil.copy2(source_root / "source-revisions.json", package / "source-revisions.json")
            target = evidence / name
            shutil.copytree(source_root / "evidence" / name, target)
            command_path = target / "container-command.json"
            command = json.loads(command_path.read_text())
            image_ref = auditor.docker_run_image_reference(command)
            self.assertEqual(image_ref, "agent-interface-3311-runtime-v2:20260920")
            command[command.index(image_ref)] = "other-image:unrelated"
            command_path.write_text(json.dumps(command, indent=2) + "\n")

            _refresh_raw_manifest_for_test(target)

            report = auditor.audit(target)
            self.assertEqual(report["checks"]["image_id_pinned"], True)
            self.assertEqual(report["checks"]["raw_manifest_matches"], True)
            self.assertEqual(report["checks"]["run_image_matches_inspect"], False)
            self.assertEqual(report["disposition"], "FAIL_AUDIT")

    def test_audit_correlates_runner_events_with_broker_response(self):
        source_root = Path(__file__).resolve().parent
        name = "20260920-v1-transport-audit-01"
        with tempfile.TemporaryDirectory(prefix="3311-v1-response-binding-") as temp:
            package = Path(temp) / source_root.name
            evidence = package / "evidence"
            evidence.mkdir(parents=True)
            shutil.copy2(source_root / "source-revisions.json", package / "source-revisions.json")
            target = evidence / name
            shutil.copytree(source_root / "evidence" / name, target)

            response_path = next((target / "ipc").glob("*.response.jsonl"))
            response = [json.loads(line) for line in response_path.read_text().splitlines()]
            response[1]["item"]["text"] = "tampered response, manifest refreshed"
            response_path.write_text("".join(json.dumps(row) + "\n" for row in response))
            _refresh_raw_manifest_for_test(target)

            report = auditor.audit(target)
            self.assertTrue(report["checks"]["raw_manifest_matches"])
            self.assertFalse(report["checks"]["runner_events_match_broker_response"])
            self.assertEqual(report["disposition"], "FAIL_AUDIT")


class ResponseCorrelationTest(unittest.TestCase):
    def test_response_must_exactly_match_runner_events(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-response-events-") as temp:
            path = Path(temp) / "response.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "synthetic"},
                {"type": "turn.completed", "usage": {"input_tokens": 1}},
            ]
            path.write_text("".join(json.dumps(row) + "\n" for row in events))
            self.assertTrue(auditor.response_matches_runner(path, events))
            self.assertFalse(auditor.response_matches_runner(path, events[:1]))
            path.write_text("not-json\n")
            self.assertFalse(auditor.response_matches_runner(path, events))
            self.assertFalse(auditor.response_matches_runner(Path(temp) / "missing", events))


class RequestPlanCorrelationTest(unittest.TestCase):
    def test_request_fields_must_match_runner_plan(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-request-plan-") as temp:
            root = Path(temp)
            request = root / "request.json"
            plan = root / "plan.json"
            payload = {"request_id": "abc", "mode": "handle", "prompt": "same\\n",
                "working": "/repo/workspace", "image": None, "image_sha256": None,
                "instructions": "/repo/instructions.txt", "instructions_sha256": "i" * 64,
                "schema": "/repo/schema.json", "schema_sha256": "s" * 64,
                "authority_granted": False}
            plan.write_text(json.dumps(payload))
            request.write_text(json.dumps(payload))
            self.assertTrue(auditor.request_matches_plan(request, plan))
            request.write_text(json.dumps(dict(payload, prompt="different\\n")))
            self.assertFalse(auditor.request_matches_plan(request, plan))
            request.write_text("not-json\n")
            self.assertFalse(auditor.request_matches_plan(request, plan))


class CurrentAuditorSidecarTest(unittest.TestCase):
    def test_three_portable_sidecars_match_all_current_checks(self):
        root = Path(__file__).resolve().parent
        for index in range(1, 4):
            name = f"20260920-v1-transport-audit-0{index}"
            with self.subTest(bundle=name):
                report = auditor.audit(root / "evidence" / name)
                sidecar = json.loads((root / "audit-reports" /
                    f"20260920-portable-reaudit-0{index}.json").read_text())
                self.assertEqual(sidecar["checks"], report["checks"])
                self.assertEqual(sidecar["disposition"], report["disposition"])


if __name__ == "__main__":
    unittest.main()
