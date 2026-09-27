import unittest
from validate_receipt import validate

VALID = {
    "schema": "agent-interface/live-adapter-authority-receipt-v1",
    "status": "DECLARED",
    "scope": "one bounded Chromium adapter run",
    "owner": {"principal": "research-owner", "purpose": "Issue-2337"},
    "provider": {"name": "provider", "model": "model", "effort": "low"},
    "fixture": {"kind": "linux-x11-chromium", "disposable": True, "display_scope": "private-xvfb"},
    "effect_scorer": {"independent": True, "retention": "retained/results"},
    "release": {"owner": "runner", "verified": False},
    "source_identities": {
        "preflight_commit": "7ba338e890846f7e508aa1cc6fd79840efd070b8",
        "preflight_status": "PASS_PRECHECK_HOLD_NO_MODEL_AUTHORITY",
    },
}

class ReceiptTests(unittest.TestCase):
    def test_declared_receipt_is_valid(self):
        self.assertEqual(validate(VALID), (True, "DECLARED_VALID"))

    def test_missing_receipt_fails_closed(self):
        self.assertEqual(validate(None)[0], False)
        self.assertEqual(validate({})[1], "RECEIPT_FIELDS_MISMATCH")

    def test_non_declared_status_never_authorizes(self):
        row = dict(VALID, status="ABSENT")
        self.assertEqual(validate(row), (False, "AUTHORITY_NOT_DECLARED"))

    def test_wrong_fixture_and_source_fail_closed(self):
        row = dict(VALID, fixture=dict(VALID["fixture"], disposable=False))
        self.assertEqual(validate(row)[0], False)
        row = dict(VALID, source_identities=dict(VALID["source_identities"], preflight_commit="bad"))
        self.assertEqual(validate(row)[0], False)

if __name__ == "__main__":
    unittest.main()
