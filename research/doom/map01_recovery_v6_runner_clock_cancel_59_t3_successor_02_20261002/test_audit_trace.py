"""Auditor mutation controls; these do not invoke the candidate or external effects."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
import unittest

import audit_trace


def source_manifest():
    result = {}
    for name, path in audit_trace.SOURCES.items():
        raw = subprocess.check_output(["git", "show", f"{audit_trace.BASE}:{path}"])
        result[name] = {"path": path, "git_blob": audit_trace.git("rev-parse", f"{audit_trace.BASE}:{path}"),
                        "sha256": hashlib.sha256(raw).hexdigest()}
    return result


def base_raw():
    now = 20_000_000_000
    def row(name, delay, lease, release, returned, cancel_observed, matched, status):
        fid = name + "-fallback"
        events = [
            {"event": "cancel_requested", "id": fid, "matched": matched},
            {"event": "input_released", "id": fid, "verified": True, "release_ns": release},
            {"event": "terminal", "id": fid, "status": status, "release": {"verified": True}},
        ]
        return {"case": name, "planner_wait_ms": 600, "clock_delay_ms": delay, "lease_ms": lease,
            "planner_start_ns": now, "timer_expired_ns": now + 600_000_000,
            "clock_return_ns": returned, "planner_end_ns": returned, "cancel_observed_ns": cancel_observed,
            "release_ns": release, "terminal_release_verified": True, "events": events,
            "runner_arm_summary": {"fallback_id": fid, "planner_window": {"end_ns": returned}}}
    a_return = now + 1_000_000_000
    a_release = a_return + 1_000_000
    b_release = now + 1_500_000_000
    b_return = now + 2_200_000_000
    cases = [row("A-clock-before-cancel-within-lease", 400, 2000, a_release, a_return,
                 a_release, True, "cancelled"),
             row("B-lease-before-clock-return", 1600, 1500, b_release, b_return,
                 None, False, "expired")]
    return {"schema": "map01-v6-runner-shared-clock-t3u-v1", "allocation": audit_trace.ALLOCATION,
        "base_commit": audit_trace.BASE, "candidate_invocations": 1, "retries": 0,
        "source_manifest": source_manifest(), "cases": cases}


class AuditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze_bytes = (audit_trace.HERE / "FREEZE.json").read_bytes()
        cls.freeze = json.loads(cls.freeze_bytes)

    def run_audit(self, raw):
        raw = copy.deepcopy(raw)
        raw["freeze_sha256"] = hashlib.sha256(self.freeze_bytes).hexdigest()
        raw["frozen_candidate_sha256"] = self.freeze["candidate_sha256"]
        raw["frozen_auditor_sha256"] = self.freeze["auditor_sha256"]
        return audit_trace.audit(raw, self.freeze, self.freeze_bytes)

    def test_synthetic_valid_fixture_passes(self):
        self.assertEqual(self.run_audit(base_raw())["status"], "PASS_RUNNER_CLOCK_DELAY_SCOPED")

    def test_wrong_returned_clock_binding_fails(self):
        raw = base_raw(); raw["cases"][0]["clock_return_ns"] += 1
        self.assertIn("returned_value_binding:A-clock-before-cancel-within-lease",
                      self.run_audit(raw)["errors"])

    def test_missing_case_fails(self):
        raw = base_raw(); raw["cases"].pop()
        self.assertIn("case_count", self.run_audit(raw)["errors"])

    def test_false_release_receipt_fails(self):
        raw = base_raw(); raw["cases"][0]["events"][1]["verified"] = False
        self.assertIn("release_receipt:A-clock-before-cancel-within-lease",
                      self.run_audit(raw)["errors"])

    def test_wrong_lease_deadline_fails(self):
        raw = base_raw(); raw["cases"][1]["release_ns"] += 100_000_000
        raw["cases"][1]["events"][1]["release_ns"] += 100_000_000
        self.assertIn("B_release_not_at_lease_deadline", self.run_audit(raw)["errors"])

    def test_late_cancel_must_be_unmatched(self):
        raw = base_raw(); raw["cases"][1]["events"][0]["matched"] = True
        self.assertIn("B_cancel_was_matched", self.run_audit(raw)["errors"])

    def test_source_hash_mismatch_fails(self):
        raw = base_raw(); raw["source_manifest"]["lease"]["git_blob"] = "0" * 40
        self.assertIn("raw_source_blob:lease", self.run_audit(raw)["errors"])


if __name__ == "__main__":
    unittest.main()
