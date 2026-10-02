"""Mutation tests for audit gates; no candidate or external effects are invoked."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import tempfile
import unittest

import audit_trace


class AuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = {
            "candidate_sha256": hashlib.sha256((audit_trace.HERE / "run_experiment.py").read_bytes()).hexdigest(),
            "auditor_sha256": hashlib.sha256((audit_trace.HERE / "audit_trace.py").read_bytes()).hexdigest(),
            "source_manifest": {},
        }
        for name, path in audit_trace.SOURCES.items():
            src = audit_trace.subprocess.check_output(["git", "show", f"{audit_trace.BASE}:{path}"])
            blob = audit_trace.git("rev-parse", f"{audit_trace.BASE}:{path}")
            cls.freeze["source_manifest"][name] = {"path": path, "git_blob": blob,
                "sha256": hashlib.sha256(src).hexdigest()}

    def positive_fixture(self):
        now = 10_000_000_000
        manifest = copy.deepcopy(self.freeze["source_manifest"])
        def row(name, delay, lease, release, end, cancel, matched, status):
            fid = name + "-fallback"
            events = [
                {"event": "cancel_requested", "id": fid, "matched": matched},
                {"event": "input_released", "id": fid, "verified": True, "release_ns": release},
                {"event": "terminal", "id": fid, "status": status, "release": {"verified": True}},
            ]
            summary = {"fallback_id": fid, "planner_window": {"end_ns": end}}
            return {"case": name, "planner_wait_ms": 600, "clock_delay_ms": delay, "lease_ms": lease,
                "planner_start_ns": now, "timer_started_ns": now, "timer_expired_ns": now + 600_000_000,
                "clock_return_ns": end, "planner_end_ns": end, "cancel_observed_ns": cancel,
                "release_ns": release, "terminal_release_verified": True, "fallback_terminal_status": status,
                "events": events, "runner_arm_summary": summary}
        a_release = now + 1_015_000_000
        b_release = now + 1_500_000_000
        cases = [row("A-clock-before-cancel-within-lease", 400, 2000, a_release,
                     now + 1_000_000_000, a_release, True, "cancelled"),
                 row("B-lease-before-clock-return", 1600, 1500, b_release,
                     now + 2_200_000_000, None, False, "expired")]
        return {"schema": "map01-v6-runner-clock-cancel-t3-successor-v1", "allocation": audit_trace.ALLOCATION,
            "base_commit": audit_trace.BASE, "candidate_invocations": 1, "retries": 0,
            "source_manifest": manifest, "cases": cases}

    def run_audit(self, raw):
        with tempfile.TemporaryDirectory() as d:
            freeze = copy.deepcopy(self.freeze)
            freeze_path = pathlib.Path(d) / "FREEZE.json"
            freeze_path.write_text(json.dumps(freeze))
            actual_path = audit_trace.HERE / "FREEZE.json"
            # Audit reads the package freeze directly; bind the fixture only during this pure test.
            original_read = pathlib.Path.read_bytes
            try:
                def read_bytes(path):
                    if path == actual_path:
                        return freeze_path.read_bytes()
                    return original_read(path)
                pathlib.Path.read_bytes = read_bytes
                raw = copy.deepcopy(raw)
                raw["freeze_sha256"] = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
                raw["frozen_candidate_sha256"] = freeze["candidate_sha256"]
                raw["frozen_auditor_sha256"] = freeze["auditor_sha256"]
                return audit_trace.audit(raw, freeze)
            finally:
                pathlib.Path.read_bytes = original_read

    def test_preregistered_fixture_passes(self):
        self.assertEqual(self.run_audit(self.positive_fixture())["status"], "PASS_RUNNER_CLOCK_DELAY_SCOPED")

    def test_drop_case_fails(self):
        raw = self.positive_fixture(); raw["cases"].pop()
        self.assertIn("case_count", self.run_audit(raw)["errors"])

    def test_false_release_fails(self):
        raw = self.positive_fixture(); raw["cases"][0]["events"][1]["verified"] = False
        self.assertIn("release_receipt:A-clock-before-cancel-within-lease", self.run_audit(raw)["errors"])

    def test_mutated_source_identity_fails(self):
        raw = self.positive_fixture(); raw["source_manifest"]["executor"]["git_blob"] = "0" * 40
        self.assertIn("source_blob:executor", self.run_audit(raw)["errors"])

    def test_late_release_fails(self):
        raw = self.positive_fixture(); raw["cases"][1]["release_ns"] += 100_000_000
        raw["cases"][1]["events"][1]["release_ns"] += 100_000_000
        self.assertIn("B_lease_deadline", self.run_audit(raw)["errors"])

    def test_wrong_cancel_match_fails(self):
        raw = self.positive_fixture(); raw["cases"][1]["events"][0]["matched"] = True
        self.assertIn("B_cancel_matched", self.run_audit(raw)["errors"])


if __name__ == "__main__":
    unittest.main()
