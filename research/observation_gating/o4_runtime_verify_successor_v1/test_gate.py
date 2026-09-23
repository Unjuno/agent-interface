import unittest
from .gate import evaluate

class O4GateTests(unittest.TestCase):
    def test_current_true_false_suppress(self):
        for decision in ("TRUE","FALSE"):
            r=evaluate({"decision":decision,"observation_id":"o1","intent_epoch":7},"o1",7)
            self.assertFalse(r["escalate"])
            self.assertEqual(r["authority_grants"],0)
    def test_unknown_and_invalid_escalate(self):
        for receipt in ({"decision":"UNKNOWN","observation_id":"o1","intent_epoch":7},{"decision":"MAYBE","observation_id":"o1","intent_epoch":7},{}):
            self.assertTrue(evaluate(receipt,"o1",7)["escalate"])
    def test_stale_mismatch_and_authority_escalate(self):
        self.assertTrue(evaluate({"decision":"TRUE","observation_id":"old","intent_epoch":7},"o1",7)["escalate"])
        self.assertTrue(evaluate({"decision":"TRUE","observation_id":"o1","intent_epoch":6},"o1",7)["escalate"])
        self.assertTrue(evaluate({"decision":"TRUE","observation_id":"o1","intent_epoch":7,"authority_grants":1},"o1",7)["escalate"])

if __name__ == "__main__":
    unittest.main()
