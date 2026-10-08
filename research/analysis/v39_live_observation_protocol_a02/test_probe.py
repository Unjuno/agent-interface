"""Turn identity and image payload checks for the loopback protocol probe."""
import unittest
from .probe import inspect_requests, turn_id_from_reply

class DeliveryAssertions(unittest.TestCase):
    def setUp(self):
        self.requests=[
          {"input":[{"type":"input_text","text":"initial"}]},
          {"input":[{"type":"function_call_output","output":[
            {"type":"input_text","text":"Fresh observation seq=200; HUD health 51, ammo 38."},
            {"type":"input_image","image_url":"data:image/png;base64,ZmFrZQ=="}]}]},
        ]
    def test_turn_id_reply_extraction(self):
        self.assertEqual(turn_id_from_reply({"result":{"turn":{"id":"turn-a"}}}),"turn-a")
    def test_missing_turn_id_is_not_accepted_as_identity(self):
        self.assertIsNone(turn_id_from_reply({"result":{}}))
    def test_equal_external_id_is_verified(self):
        summary=inspect_requests(self.requests,b"fake","seq=200","turn-a","turn-a")
        self.assertTrue(summary["same_turn_id"])
    def test_mismatched_external_id_is_rejected(self):
        summary=inspect_requests(self.requests,b"fake","seq=200","turn-a","turn-b")
        self.assertFalse(summary["same_turn_id"])
    def test_text_and_image_payload_checks(self):
        summary=inspect_requests(self.requests,b"fake","seq=200","turn-a","turn-a")
        self.assertTrue(summary["text_delivered"])
        self.assertTrue(summary["image_delivered"])
        self.assertTrue(summary["image_in_second_request"])

if __name__=="__main__": unittest.main(verbosity=2)
