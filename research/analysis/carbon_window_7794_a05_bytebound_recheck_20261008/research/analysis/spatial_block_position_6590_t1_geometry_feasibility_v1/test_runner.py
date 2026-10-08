from __future__ import annotations

import json
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "recovery_02"))
from runner import docker_create, runtime_settings


class RecoveryRunnerTests(unittest.TestCase):
    def test_recovery_freeze_hashes_all_sources_and_stop_provenance(self):
        recovery = ROOT / "recovery_02"
        freeze = json.loads((recovery / "FREEZE.json").read_text(encoding="utf-8"))
        freeze_sha = (recovery / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
        self.assertEqual(hashlib.sha256((recovery / "FREEZE.json").read_bytes()).hexdigest(), freeze_sha)
        for relative, expected in freeze["source_sha256"].items():
            self.assertEqual(hashlib.sha256((recovery / relative).resolve().read_bytes()).hexdigest(), expected, relative)
        self.assertEqual(hashlib.sha256((ROOT / "results/preflight-01/STOP.json").read_bytes()).hexdigest(),
                         freeze["source_sha256"]["../results/preflight-01/STOP.json"])

    def test_nested_frozen_settings_are_read_without_top_level_alias(self):
        resources = {"cpus": 1, "memory": "256m", "pids": 32}
        environment = {"image": "frozen-image", "resource_limits": resources}
        actual_environment, actual_resources = runtime_settings({"environment": environment})
        self.assertIs(actual_environment, environment)
        self.assertIs(actual_resources, resources)

    def test_docker_command_binds_all_frozen_isolation_controls(self):
        resources = {"cpus": 1, "memory": "256m", "pids": 32}
        command = docker_create("frozen-image", "fresh-candidate", ["python", "candidate.py"],
                                ["type=bind,src=/repo,dst=/src,readonly"], resources)
        for required in ("--network", "none", "--cpus", "1", "--memory", "256m",
                         "--pids-limit", "32", "--read-only", "--cap-drop", "ALL",
                         "--security-opt", "no-new-privileges"):
            self.assertIn(required, command)
        self.assertIn("type=bind,src=/repo,dst=/src,readonly", command)
        self.assertNotIn("--rm", command)

    def test_allocation_01_stop_confirms_no_candidate_or_container_started(self):
        stop = json.loads((ROOT / "results/preflight-01/STOP.json").read_text(encoding="utf-8"))
        self.assertEqual(stop["candidate_invocations"], 0)
        self.assertEqual(stop["auditor_invocations"], 0)
        self.assertEqual(stop["containers_created"], 0)
        self.assertFalse(stop["freeze_modified_or_reused"])


if __name__ == "__main__":
    unittest.main()
