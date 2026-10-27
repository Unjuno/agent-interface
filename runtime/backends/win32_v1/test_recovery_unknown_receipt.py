"""Recovery receipt tests using inert backend data only."""
import unittest
from runtime.backends.win32_v1.session import Win32RuntimeSession

class Backend:
    def __init__(self,receipt): self.receipt=receipt; self.emissions=0
    def release_all(self): return self.receipt

class RecoveryUnknownReceiptTests(unittest.TestCase):
    def test_unknown_or_missing_state_never_clears_recovery(self):
        for extra in ({"keys_unknown":["Q"],"buttons_unknown":[]},
                      {"keys_unknown":[],"buttons_unknown":["left"]},
                      {}, {"keys_unknown":[],"buttons_unknown":None}):
            with self.subTest(extra=extra):
                receipt={"verified":True,"keys_down":[],"buttons_down":[],**extra}
                session=Win32RuntimeSession(Backend(receipt));session.recovery_required=True
                row=session.recover_input()
                self.assertEqual(row["status"],"recovery_failed")
                self.assertTrue(row["recovery_required"])
                self.assertFalse(row["replay_allowed"])

    def test_unknown_terminal_receipt_does_not_clear_inflight_recovery(self):
        receipt={"verified":True,"keys_down":[],"buttons_down":[],"keys_unknown":["Q"],"buttons_unknown":[]}
        session=Win32RuntimeSession(Backend(receipt));session.recovery_required=True
        session._recovery_requested_during_dispatch=True
        self.assertFalse(session._record_release([receipt]))
        self.assertTrue(session.recovery_required)
        self.assertTrue(session._recovery_requested_during_dispatch)

    def test_explicit_known_empty_receipt_can_clear_recovery(self):
        receipt={"verified":True,"keys_down":[],"buttons_down":[],"keys_unknown":[],"buttons_unknown":[]}
        session=Win32RuntimeSession(Backend(receipt));session.recovery_required=True
        row=session.recover_input()
        self.assertEqual(row["status"],"input_recovered")
        self.assertFalse(row["recovery_required"])

if __name__=="__main__":unittest.main()
