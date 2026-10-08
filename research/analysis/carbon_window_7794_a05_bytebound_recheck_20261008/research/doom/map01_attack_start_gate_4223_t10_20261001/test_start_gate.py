from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import ModuleType
from unittest.mock import patch

from audit_start_gate import audit
from verify_artifact import safe_rel


RGB_FIXTURE = b"deterministic synthetic RGB pixels"


class FakeImage:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def convert(self, mode):
        if mode != "RGB":
            raise AssertionError(mode)
        return self

    def tobytes(self):
        return RGB_FIXTURE


def fake_pillow():
    module = ModuleType("PIL")
    module.Image = type("ImageModule", (), {"open": staticmethod(lambda _path: FakeImage())})
    return module


class StartGateAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.raw_path = self.root / "RAW.json"
        self.manifest_path = self.root / "manifest.json"
        self.image_path = self.root / "initial.png"
        self.freeze_path = self.root / "FREEZE.json"
        self.report_path = self.root / "AUDIT.json"
        self.image_path.write_bytes(b"synthetic PNG placeholder; runtime container checks real PNG bytes")
        rgb_hash = hashlib.sha256(RGB_FIXTURE).hexdigest()
        self.freeze_path.write_text(json.dumps({
            "allocation": "MAP01-ATTACK-ONSET-STARTGATE-4223-T10-20261001-01",
            "runtime_artifact_id": 10398313098,
            "runtime_artifact_sha256": "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b",
            "runtime_source_base": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
        }))
        freeze_hash = hashlib.sha256(self.freeze_path.read_bytes()).hexdigest()
        sources = {f"doom/source_{i}.py": f"{i:064x}" for i in range(15)}
        files = {"research/" + key: {"sha256": value} for key, value in sources.items()}
        self.manifest_path.write_text(json.dumps({
            "base_commit": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245", "files": files,
        }))
        self.stdout_path = self.root / "child.stdout.jsonl"
        self.stderr_path = self.root / "child.stderr.txt"
        self.execution_path = self.root / "OBSTAC_EXECUTION.json"
        self.raw = {
            "schema": "map01-attack-start-gate-raw-v1",
            "allocation": "MAP01-ATTACK-ONSET-STARTGATE-4223-T10-20261001-01",
            "decision": "PASS_START_GATE_ONLY", "failure": None,
            "runtime_artifact_id": 10398313098,
            "runtime_artifact_sha256": "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b",
            "runtime_source_base": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
            "candidate_invocations": 1, "retry_count": 0,
            "architecture": "x86_64", "python": "3.13.5 (fixture)", "vizdoom": "1.3.0",
            "environment": {
                "OBSTAC_SOURCE_COMMIT": "abc", "OBSTAC_IMAGE_ID": "sha256:def",
                "OBSTAC_FREEZE_SHA256": freeze_hash, "OBSTAC_CONSTRUCTION": "0",
                "OBSTAC_PLATFORM": "linux/amd64", "OBSTAC_DOCKER_CONTEXT": "github-actions",
                "OBSTAC_RUNTIME_SOURCE_BASE": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
            },
            "events": [
                {"event": "ready"},
                {"event": "observation", "id": "initial", "sequence": 1,
                 "exact": True, "frame_rgb_sha256": rgb_hash},
                {"event": "command", "command": {"op": "finish"}},
                {"event": "post_control_score"},
            ],
            "sent_commands": [{"op": "finish"}], "child_returncode": 0,
            "input_admission_count": 0, "post_control_score_count": 1,
            "runtime_sources": sources,
            "initial_observation_png_sha256": hashlib.sha256(self.image_path.read_bytes()).hexdigest(),
            "child_stdout_sha256": "b" * 64, "child_stderr_sha256": "c" * 64,
        }
        self.stdout_path.write_text("".join(json.dumps(event) + "\n" for event in self.raw["events"]))
        self.stderr_path.write_bytes(b"")
        self.raw["child_stdout_sha256"] = hashlib.sha256(self.stdout_path.read_bytes()).hexdigest()
        self.raw["child_stderr_sha256"] = hashlib.sha256(self.stderr_path.read_bytes()).hexdigest()
        self.raw["runtime_sources_sha256"] = hashlib.sha256(
            (json.dumps(sources, indent=2, sort_keys=True) + "\n").encode()
        ).hexdigest()
        self.execution_path.write_text(json.dumps({
            "schema": "obstac-map01-start-gate-execution-v1",
            "allocation": "MAP01-ATTACK-ONSET-STARTGATE-4223-T10-20261001-01",
            "source_commit": "abc", "image_id": "sha256:def", "candidate_exit_code": 0,
            "formal_candidate_invocations": 1, "independent_auditor_invocations": 1,
            "candidate_retry_budget": 0, "formal_status": "AUDITOR_ARMED",
            "runtime_artifact": {"artifact_id": 10398313098,
                                 "artifact_sha256": "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b"},
            "image_platform": "linux/amd64",
            "candidate_mount_probe_invocations": 1, "candidate_mount_probe_exit_code": 0,
            "candidate_output_host_mode": "0o777", "candidate_mount_probe_output": {"uid": 0, "gid": 0, "mode": "0o777"},
            "candidate_mount_probe_argv": ["docker", "run", "--network", "none", "--cap-drop", "ALL"],
            "auditor_mount_probe_invocations": 1, "auditor_mount_probe_exit_code": 0,
            "auditor_output_host_mode": "0o777", "auditor_mount_probe_output": {"uid": 0, "gid": 0, "mode": "0o777"},
            "auditor_mount_probe_argv": ["docker", "run", "--network", "none", "--cap-drop", "ALL"],
            "candidate_argv": ["docker", "run", "--network", "none", "--read-only",
                               "--platform", "linux/amd64", "--mount", "type=bind,src=/src,dst=/src,readonly"],
            "auditor_argv": ["docker", "run", "--network", "none", "--read-only",
                             "--platform", "linux/amd64"],
        }))
        self.write_raw()

    def tearDown(self):
        self.temp.cleanup()

    def write_raw(self):
        self.raw_path.write_text(json.dumps(self.raw))

    def run_audit(self):
        receipt_env = {
            "OBSTAC_SOURCE_COMMIT": "abc", "OBSTAC_IMAGE_ID": "sha256:def",
            "OBSTAC_FREEZE_SHA256": "a" * 64, "OBSTAC_DOCKER_CONTEXT": "github-actions",
            "OBSTAC_RUNTIME_SOURCE_BASE": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
        }
        receipt_env["OBSTAC_FREEZE_SHA256"] = hashlib.sha256(self.freeze_path.read_bytes()).hexdigest()
        with patch.dict(sys.modules, {"PIL": fake_pillow()}), patch.dict(os.environ, receipt_env):
            return audit(self.raw_path, self.manifest_path, self.image_path, self.freeze_path,
                         self.stdout_path, self.stderr_path, self.execution_path, self.report_path)

    def test_exact_startup_evidence_passes(self):
        report = self.run_audit()
        self.assertEqual(report["decision"], "PASS_START_GATE_ONLY")
        self.assertEqual(report["errors"], [])

    def test_rejects_missing_observation(self):
        self.raw["events"].pop(1)
        self.write_raw()
        report = self.run_audit()
        self.assertIn("one_initial_observation", report["errors"])

    def test_rejects_non_finish_command(self):
        self.raw["sent_commands"] = [{"op": "submit"}]
        self.write_raw()
        report = self.run_audit()
        self.assertIn("finish_only", report["errors"])

    def test_rejects_child_nonzero_exit(self):
        self.raw["child_returncode"] = 1
        self.write_raw()
        report = self.run_audit()
        self.assertIn("child_exit_zero", report["errors"])

    def test_rejects_unbound_runtime_source(self):
        self.raw["runtime_sources"]["doom/source_0.py"] = "f" * 64
        self.write_raw()
        report = self.run_audit()
        self.assertIn("runtime_source_hashes", report["errors"])

    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            safe_rel("../escape")

    def test_rejects_candidate_output_permission_not_proven(self):
        receipt = json.loads(self.execution_path.read_text())
        receipt["candidate_mount_probe_exit_code"] = 1
        self.execution_path.write_text(json.dumps(receipt))
        report = self.run_audit()
        self.assertIn("candidate_output_mount_probe", report["errors"])

    def test_rejects_auditor_output_permission_not_proven(self):
        receipt = json.loads(self.execution_path.read_text())
        receipt["auditor_output_host_mode"] = "0o700"
        self.execution_path.write_text(json.dumps(receipt))
        report = self.run_audit()
        self.assertIn("auditor_output_mount_probe", report["errors"])


if __name__ == "__main__":
    unittest.main()
