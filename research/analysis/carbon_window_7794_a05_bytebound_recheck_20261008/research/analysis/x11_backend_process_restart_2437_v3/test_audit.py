import unittest

from experiment import (audit_document, classify, merge_dispatch_observation,
                        record_explicit_cleanup)


def complete(status="completed", after=2):
    return {
        "key_down_before_crash": True,
        "key_down_after_backend_crash": True,
        "worker_exit_after_kill": -9,
        "new_session_recovery_required_initial": False,
        "stale_dispatch": {"status": status},
        "emissions_before_stale_dispatch": 0,
        "emissions_after_stale_dispatch": after,
        "key_down_after_explicit_cleanup": False,
        "cleanup_owner": "independent-observer-connection",
        "server_pid": 123,
        "server_pid_after_restart_boundary": 123,
        "xvfb_same_process_alive": True,
        "dispatch_now_ns": 10,
        "stale_request_expiry_ns": 20,
        "dispatch_worker_exit": 0,
        "worker_exit_before_kill": None,
        "hold_worker_ready": {"pid": 456, "session_id": "old-session"},
        "hold_worker_pid": 456,
        "hold_session_id": "old-session",
        "dispatch_session_id": "new-session",
    }


class AuditorConstructionTests(unittest.TestCase):
    def test_stale_request_admitted_is_fail(self):
        self.assertEqual(classify(complete()), ("FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED", []))

    def test_rejects_missing_independent_crash_observation(self):
        raw = complete()
        raw["key_down_after_backend_crash"] = False
        self.assertIn("crash-boundary-did-not-retain-key-down", audit_document(raw))

    def test_rejects_server_restart_substitution(self):
        raw = complete()
        raw["server_pid_after_restart_boundary"] = 124
        raw["xvfb_same_process_alive"] = False
        self.assertIn("xvfb-server-identity-not-preserved", audit_document(raw))

    def test_rejects_unverified_cleanup(self):
        raw = complete()
        raw["key_down_after_explicit_cleanup"] = True
        self.assertIn("cleanup-not-independently-neutral", audit_document(raw))

    def test_incomplete_raw_stops(self):
        self.assertEqual(classify({"schema": "incomplete"})[0], "STOP_AUDIT_ERRORS")

    def test_explicit_new_session_quarantine_and_zero_emission_is_scoped_pass(self):
        raw = complete(status="refused", after=0)
        raw["new_session_recovery_required_initial"] = True
        raw["stale_dispatch"]["error"] = "INPUT_RECOVERY_REQUIRED"
        self.assertEqual(classify(raw), ("PASS_BACKEND_RESTART_FAIL_CLOSED_SCOPED", []))

    def test_other_refusal_is_not_pass(self):
        raw = complete(status="refused", after=0)
        raw["stale_dispatch"]["error"] = "BACKEND_CONSTRAINT"
        self.assertEqual(classify(raw)[0], "STOP_INCONCLUSIVE_DISPATCH_STATE")

    def test_parent_receipt_copies_restart_clock_and_session_without_external_state(self):
        record = {}
        child = {
            "stale_dispatch": {"status": "completed"},
            "emissions_before": 0,
            "emissions_after": 2,
            "new_session_recovery_required_initial": False,
            "new_session_recovery_required_after": False,
            "request_sha256": "a" * 64,
            "pid": 123,
            "session_id": "fresh-session",
            "dispatch_now_ns": 10,
        }
        merge_dispatch_observation(record, child)
        self.assertEqual(record["dispatch_now_ns"], 10)
        self.assertEqual(record["dispatch_session_id"], "fresh-session")
        self.assertEqual(record["emissions_after_stale_dispatch"], 2)

    def test_cleanup_receipt_records_independent_observation_and_owner(self):
        record = {}
        record_explicit_cleanup(record, False)
        self.assertEqual(record["key_down_after_explicit_cleanup"], False)
        self.assertEqual(record["cleanup_owner"], "independent-observer-connection")

    def test_auditor_reports_exception_even_if_other_required_fields_are_missing(self):
        self.assertIn("candidate-harness-exception", audit_document({"harness_exception": "NameError"}))


if __name__ == "__main__":
    unittest.main()
