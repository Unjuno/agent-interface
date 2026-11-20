import unittest

from .probe import inspect_requests


class DeliveryAssertions(unittest.TestCase):
    def test_same_turn_check_reads_both_protocol_replies(self):
        requests = []
        image = b"frame"
        initial = {"result": {"turn": {"id": "turn-a", "status": "inProgress"}}}
        same_turn = {"result": {"turn": {"id": "turn-a", "status": "inProgress", "startedAt": None}}}
        other_turn = {"result": {"turn": {"id": "turn-b", "status": "inProgress"}}}
        missing_turn = {"result": {"thread": {"id": "thread-a"}}}

        same = inspect_requests(requests, image, "observation", initial, same_turn)
        different = inspect_requests(requests, image, "observation", initial, other_turn)
        missing = inspect_requests(requests, image, "observation", initial, missing_turn)
        self.assertTrue(same["same_turn_id"])
        self.assertEqual(same["initial_turn_id"], "turn-a")
        self.assertEqual(same["external_turn_id"], "turn-a")
        self.assertFalse(different["same_turn_id"])
        self.assertFalse(missing["same_turn_id"])

    def test_external_observation_is_in_second_model_request(self):
        # Pure assertion helper: no server, CLI, network, credentials, or model.
        requests = [
            {"input": [{"type": "input_text", "text": "initial"}]},
            {
                "input": [
                    {
                        "type": "function_call_output",
                        "output": [
                            {"type": "input_text", "text": "Fresh observation seq=200; HUD health 51, ammo 38."},
                            {"type": "input_image", "image_url": "data:image/png;base64,ZmFrZQ=="},
                        ],
                    }
                ]
            },
        ]
        reply = {"result": {"turn": {"id": "turn-a"}}}
        summary = inspect_requests(requests, b"fake", "seq=200", reply, reply)
        self.assertTrue(summary["same_turn_id"])
        self.assertTrue(summary["text_delivered"])
        self.assertTrue(summary["image_delivered"])


