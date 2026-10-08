import unittest
from bridge import BridgeRefused, validate

BASE = {"request_id": "r1", "authority_granted": False, "returncode": 0}
PROC = {"request_id": "r1", "authority_granted": False, "exit_code": 0}
EVENTS = [{"type": "item.completed", "content": {"json": {"ok": True}}},
          {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}]

class BridgeTests(unittest.TestCase):
    def test_accepts_one_completed_non_authoritative_turn(self):
        result = validate({"request_id": "r1"}, EVENTS, BASE, PROC)
        self.assertEqual(result["status"], "PASS_DOCKER_IPC_SCHEMA_BRIDGE")
        self.assertFalse(result["authority_granted"])

    def test_refuses_mismatch(self):
        with self.assertRaisesRegex(BridgeRefused, "request_id_mismatch"):
            validate({"request_id": "r2"}, EVENTS, BASE, PROC)

    def test_refuses_failure(self):
        with self.assertRaisesRegex(BridgeRefused, "response_contains_failure"):
            validate({"request_id": "r1"}, EVENTS + [{"type": "error"}], BASE, PROC)

if __name__ == "__main__": unittest.main()
