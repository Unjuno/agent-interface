import unittest
from .validator import validate_capsule

class CapsuleValidatorTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "session_id": "s1", "task_id": "t1", "capsule_id": "c1",
            "uncertainty": ["authority_not_transferred"],
            "replay_prohibited": True, "authority_transfer": False,
            "authority_status": "REQUIRE_FRESH", "expires_at": 100,
            "contradictory": False, "semantic_status": "PARTIAL",
        }

    def test_accepts_advisory_context_only(self):
        d = validate_capsule(self.base, session_id="s1", task_id="t1", now_epoch=10)
        self.assertEqual((d.usable, d.reason, d.requires_fresh_authority),
                         (True, "advisory_context_only", True))

    def test_rejects_identity_expiry_and_authority_controls(self):
        controls = (
            ("session_id", "s2", "session_mismatch"),
            ("task_id", "t2", "task_mismatch"),
            ("expires_at", 10, "expired"),
            ("authority_transfer", True, "authority_transfer_forbidden"),
            ("replay_prohibited", False, "replay_not_prohibited"),
            ("contradictory", True, "contradictory"),
        )
        for key, value, reason in controls:
            with self.subTest(key=key):
                c = dict(self.base); c[key] = value
                d = validate_capsule(c, session_id="s1", task_id="t1", now_epoch=10)
                self.assertEqual((d.usable, d.reason), (False, reason))

    def test_missing_or_invalid_fields_are_not_unknown_success(self):
        for key in ("uncertainty", "expires_at", "capsule_id"):
            with self.subTest(key=key):
                c = dict(self.base); c.pop(key)
                d = validate_capsule(c, session_id="s1", task_id="t1", now_epoch=10)
                self.assertFalse(d.usable)
        c = dict(self.base); c["semantic_status"] = "COMPLETED"
        self.assertEqual(validate_capsule(c, session_id="s1", task_id="t1", now_epoch=10).reason,
                         "invalid_semantic_status")

if __name__ == "__main__":
    unittest.main()
