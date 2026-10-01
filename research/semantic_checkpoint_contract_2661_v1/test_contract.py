import unittest
from checkpoint_contract import validate

BASE = {"session_id": "s1", "task_id": "t1", "epoch": 3,
        "status": "CONFIRMED", "evidence_ref": "artifact:1",
        "resume_policy": {"allowed": True, "requires_fresh_authority": True}}

class ContractTests(unittest.TestCase):
    def test_confirmed_is_review_only(self):
        d = validate(BASE, session_id="s1", task_id="t1", current_epoch=3)
        self.assertEqual((d.accepted, d.disposition), (True, "ADMITTED_FOR_REVIEW"))
    def test_provisional_and_unknown_yield(self):
        for status in ("PROVISIONAL", "UNKNOWN"):
            d = validate({**BASE, "status": status}, session_id="s1", task_id="t1", current_epoch=3)
            self.assertEqual(d.disposition, "YIELD")
    def test_binding_epoch_and_invalidation_refuse(self):
        for kwargs in ({"session_id": "other"}, {"task_id": "other"}, {"current_epoch": 2}, {"invalidations": {"stale"}}):
            args = {"session_id": "s1", "task_id": "t1", "current_epoch": 3}; args.update(kwargs)
            self.assertFalse(validate(BASE, **args).accepted)
    def test_authority_policy_cannot_be_omitted_or_relaxed(self):
        for policy in ({"allowed": True, "requires_fresh_authority": False}, {"allowed": False, "requires_fresh_authority": True}):
            self.assertFalse(validate({**BASE, "resume_policy": policy}, session_id="s1", task_id="t1", current_epoch=3).accepted)

if __name__ == "__main__":
    unittest.main()
