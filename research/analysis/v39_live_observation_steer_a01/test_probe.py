"""Unit checks for turn/steer identity and request-delivery inspection."""

from pathlib import Path
import base64
import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "v39_observation_steer_a01_probe", Path(__file__).with_name("probe.py")
)
PROBE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PROBE)


class RequestOrderTests(unittest.TestCase):
    def test_second_request_before_first_completion_is_pending_overlap(self):
        self.assertEqual(
            PROBE.classify_request_order(20, 30),
            "SECOND_REQUEST_WHILE_INITIAL_PENDING",
        )

    def test_second_request_after_first_completion_is_queued(self):
        self.assertEqual(
            PROBE.classify_request_order(31, 30),
            "SECOND_REQUEST_AFTER_INITIAL_COMPLETION",
        )

    def test_missing_second_request_remains_explicit(self):
        self.assertEqual(
            PROBE.classify_request_order(None, 30),
            "SECOND_REQUEST_NOT_OBSERVED",
        )

    def test_external_turn_identity_is_read_from_the_rpc_reply(self):
        reply = {"result": {"turn": {"id": "actual-returned-turn"}}}
        self.assertEqual(PROBE.turn_id_from_start_reply(reply), "actual-returned-turn")

    def test_steer_identity_is_read_from_its_actual_rpc_reply(self):
        reply = {"result": {"turnId": "actual-steered-turn"}}
        self.assertEqual(PROBE.turn_id_from_steer_reply(reply), "actual-steered-turn")

    def test_missing_external_turn_identity_is_not_assumed(self):
        self.assertIsNone(PROBE.turn_id_from_start_reply({"result": {}}))

    def test_missing_steer_turn_identity_is_not_assumed(self):
        self.assertIsNone(PROBE.turn_id_from_steer_reply({"result": {}}))

    def test_inspection_requires_text_and_exact_image_in_second_request(self):
        frame = b"retained frame bytes"
        image = "data:image/png;base64," + base64.b64encode(frame).decode("ascii")
        requests = [{"input": []}, {"input": [
            {"type": "message", "content": [{"type": "input_text", "text": "obs"}]},
            {"type": "message", "content": [{"type": "input_image", "image_url": image}]},
        ]}]
        inspected = PROBE.inspect_requests(requests, frame, "obs")
        self.assertTrue(inspected["text_delivered"])
        self.assertTrue(inspected["image_delivered"])
        self.assertTrue(inspected["image_in_second_request"])
        self.assertEqual(inspected["input_image_count"], 1)

    def test_inspection_rejects_content_missing_from_second_request(self):
        frame = b"retained frame bytes"
        inspected = PROBE.inspect_requests([{"input": []}, {"input": []}], frame, "obs")
        self.assertFalse(inspected["text_delivered"])
        self.assertFalse(inspected["image_delivered"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
