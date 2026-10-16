"""Unit tests for the one-shot turn/steer probe's evidence parsing."""
import base64
import hashlib
import unittest

from probe import EVENT_TEXT, classify_request_order, inspect_requests, turn_id_from_steer_reply


class TurnSteerProbeTests(unittest.TestCase):
    def test_classifies_preemptive_and_queued_delivery(self):
        self.assertEqual(classify_request_order(99, 100, 200),
                         "SECOND_REQUEST_WHILE_INITIAL_PENDING")
        self.assertEqual(classify_request_order(101, 100, 200),
                         "SECOND_REQUEST_AFTER_INITIAL_COMPLETION")

    def test_classifies_before_release_when_first_response_was_cancelled(self):
        self.assertEqual(classify_request_order(99, None, 100),
                         "SECOND_REQUEST_WHILE_INITIAL_PENDING")
        self.assertEqual(classify_request_order(101, None, 100),
                         "ORDER_UNVERIFIABLE")

    def test_missing_or_malformed_timestamps_are_not_a_pass(self):
        self.assertEqual(classify_request_order(None, 100, 200),
                         "SECOND_REQUEST_NOT_OBSERVED")
        self.assertEqual(classify_request_order("99", 100, 200), "ORDER_UNVERIFIABLE")

    def test_extracts_only_an_actual_turn_steer_reply_id(self):
        self.assertEqual(turn_id_from_steer_reply(
            {"result": {"turnId": "turn-7"}}), "turn-7")
        self.assertIsNone(turn_id_from_steer_reply(
            {"result": {"turn": {"id": "turn-7"}}}))
        self.assertIsNone(turn_id_from_steer_reply({"error": {"code": -32600}}))

    def test_checks_raw_second_request_for_exact_text_and_image(self):
        image = b"frame-png"
        data_url = "data:image/png;base64," + base64.b64encode(image).decode()
        requests = [{"input": [{"type": "message", "content": []}]},
                    {"input": [{"type": "message", "content": [
                        {"type": "input_text", "text": EVENT_TEXT},
                        {"type": "input_image", "image_url": data_url},
                    ]}]}]
        record = inspect_requests(requests, image, EVENT_TEXT)
        self.assertTrue(record["text_delivered"])
        self.assertTrue(record["image_delivered"])
        self.assertEqual(record["image_sha256"], hashlib.sha256(image).hexdigest())
        self.assertEqual(record["captured_requests"], requests)


if __name__ == "__main__":
    unittest.main(verbosity=2)
