import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate_t3v", "run_t3v.py")
auditor = load("auditor_t3v", "audit_t3v.py")


def synthetic_row(name):
    common = {"name": name, "planner_wait_ms": 600, "clock_delay_ms": 400,
              "lease_ms": 2000, "planner_start_ns": 100_000_000,
              "timer_expired_ns": 700_000_000, "clock_return_ns": 1_100_000_000,
              "planner_end_ns": 1_100_000_000, "terminal_release_verified": True,
              "runner_arm_summary": {"fallback_id": "fallback"}}
    if name == "A-clock-before-cancel-within-lease":
        common.update({"release_ns": 1_102_000_000, "cancel_observed_ns": 1_101_000_000,
                       "fallback_terminal_status": "completed",
                       "cancel_requested": {"event": "cancel_requested", "id": "fallback",
                                            "matched": True, "requested_ns": 1_100_500_000},
                       "events": [
                           {"event": "cancel_requested", "id": "fallback", "matched": True,
                            "requested_ns": 1_100_500_000},
                           {"event": "input_released", "id": "fallback", "verified": True,
                            "release_ns": 1_102_000_000},
                           {"event": "terminal", "id": "fallback", "status": "completed",
                            "terminal_ns": 1_103_000_000, "release": {"verified": True}},
                       ]})
    else:
        common.update({"clock_delay_ms": 1600, "lease_ms": 1500,
                       "clock_return_ns": 1_700_000_000, "planner_end_ns": 1_700_000_000,
                       "release_ns": 1_600_000_000, "cancel_observed_ns": None,
                       "fallback_terminal_status": "expired",
                       "cancel_requested": {"event": "cancel_requested", "id": "fallback",
                                            "matched": False, "requested_ns": 1_700_500_000},
                       "events": [
                           {"event": "input_released", "id": "fallback", "verified": True,
                            "release_ns": 1_600_000_000},
                           {"event": "terminal", "id": "fallback", "status": "expired",
                            "terminal_ns": 1_601_000_000, "release": {"verified": True}},
                           {"event": "cancel_requested", "id": "fallback", "matched": False,
                            "requested_ns": 1_700_500_000},
                       ]})
    return common


class CandidateGateTests(unittest.TestCase):
    def test_cooperative_return_is_completed_not_cancelled(self):
        self.assertEqual(candidate.gate_errors(synthetic_row("A-clock-before-cancel-within-lease")), [])

    def test_cancelled_terminal_rejected_for_cooperative_return(self):
        row = synthetic_row("A-clock-before-cancel-within-lease")
        row["fallback_terminal_status"] = "cancelled"
        self.assertIn("COOPERATIVE_TERMINAL_NOT_COMPLETED", candidate.gate_errors(row))

    def test_lease_expiry_then_unmatched_cancel(self):
        self.assertEqual(candidate.gate_errors(synthetic_row("B-lease-before-clock-return")), [])

    def test_matched_late_cancel_rejected(self):
        row = synthetic_row("B-lease-before-clock-return")
        row["cancel_requested"]["matched"] = True
        self.assertIn("B_LATE_CANCEL_NOT_UNMATCHED", candidate.gate_errors(row))


class IndependentOracleTests(unittest.TestCase):
    def freeze(self):
        return {"package_sha256": {}, "source_manifest": {}}

    def payload(self):
        cases = []
        for name, expected in auditor.EXPECTED.items():
            cases.append({"row": {**synthetic_row(name), **expected}, "gate_errors": []})
        return {"allocation": auditor.ALLOCATION, "base_commit": auditor.BASE,
                "candidate_invocations": 1, "retries": 0, "package_sha256": {},
                "source_manifest": {}, "freeze_sha256": auditor.sha256((HERE / "FREEZE.json").read_bytes())
                    if (HERE / "FREEZE.json").exists() else "fixture-freeze",
                "cases": cases, "candidate_gate_errors": [], "status": "PASS_CANDIDATE_GATES"}

    def test_oracle_accepts_declared_controls(self):
        payload = self.payload()
        # Test the case-level raw oracle without depending on an allocation freeze file.
        for item in payload["cases"]:
            self.assertEqual(auditor.audit_case(item["row"], auditor.EXPECTED[item["row"]["name"]]), [])

    def test_oracle_rejects_status_or_lineage_mutation(self):
        row = synthetic_row("A-clock-before-cancel-within-lease")
        row["events"][-1]["status"] = "cancelled"
        self.assertIn("A_COOPERATIVE_TERMINAL_STATUS",
                      auditor.audit_case(row, auditor.EXPECTED[row["name"]]))

    def test_oracle_rejects_lease_released_after_clock_return(self):
        row = synthetic_row("B-lease-before-clock-return")
        row["events"][0]["release_ns"] = row["clock_return_ns"] + 1
        row["release_ns"] = row["events"][0]["release_ns"]
        errors = auditor.audit_case(row, auditor.EXPECTED[row["name"]])
        self.assertIn("B_RELEASE_NOT_PRE_RETURN", errors)


if __name__ == "__main__":
    unittest.main()
