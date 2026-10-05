import unittest

from .probe import inspect_requests


class DeliveryAssertions(unittest.TestCase):
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
        summary = inspect_requests(requests, b"fake", "seq=200", "turn-a", "turn-a")
        self.assertTrue(summary["same_turn_id"])
        self.assertTrue(summary["text_delivered"])
        self.assertTrue(summary["image_delivered"])
