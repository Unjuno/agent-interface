import unittest

from experiment import audit_document, classify


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


if __name__ == "__main__":
    unittest.main()
