"""Tests for A02's ordering decision, independent of the App Server."""

from pathlib import Path
import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "v39_observation_a02_probe", Path(__file__).with_name("probe.py")
)
PROBE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PROBE)


class RequestOrderTests(unittest.TestCase):
    def test_probe_exposes_a_request_order_classifier(self):
        self.assertTrue(
            callable(getattr(PROBE, "classify_request_order", None)),
            "A02 must distinguish a second request while the first is pending",
        )

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

    def test_missing_external_turn_identity_is_not_assumed(self):
        self.assertIsNone(PROBE.turn_id_from_start_reply({"result": {}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
