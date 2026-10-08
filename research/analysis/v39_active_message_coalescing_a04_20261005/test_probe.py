"""Tests for the A04 delivery classifier, independent of the App Server."""

from pathlib import Path
import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "v39_observation_a02_probe", Path(__file__).with_name("probe.py")
)
PROBE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PROBE)


def delivery(sequence, request_index, text_position, image_position):
    return {
        "observation_seq": sequence,
        "request_index": request_index,
        "paired": True,
        "text_seen": True,
        "image_seen": True,
        "text_position": text_position,
        "image_position": image_position,
    }


class DeliveryClassificationTests(unittest.TestCase):
    def test_both_paired_observations_in_one_followup_keep_order(self):
        self.assertEqual(
            PROBE.classify_deliveries([
                delivery(201, 1, 10, 20), delivery(202, 1, 30, 40),
            ]),
            "BOTH_IN_ONE_FOLLOWUP_ORDERED",
        )

    def test_both_paired_observations_across_followups_keep_order(self):
        self.assertEqual(
            PROBE.classify_deliveries([
                delivery(201, 1, 10, 20), delivery(202, 2, 3, 8),
            ]),
            "BOTH_ACROSS_FOLLOWUPS_ORDERED",
        )

    def test_latest_only_is_distinguished_from_first_only(self):
        latest = delivery(202, 1, 10, 20)
        first = delivery(201, 1, 10, 20)
        missing = {"paired": False, "text_seen": False, "image_seen": False}
        self.assertEqual(PROBE.classify_deliveries([missing, latest]), "LATEST_ONLY")
        self.assertEqual(PROBE.classify_deliveries([first, missing]), "FIRST_ONLY")

    def test_text_without_its_image_is_not_counted_as_a_paired_delivery(self):
        partial = {
            "paired": False, "text_seen": True, "image_seen": False,
            "request_index": 1, "text_position": 10, "image_position": -1,
        }
        self.assertEqual(
            PROBE.classify_deliveries([partial, partial]),
            "PARTIAL_OR_UNVERIFIABLE",
        )

    def test_missing_or_reversed_delivery_is_not_promoted(self):
        missing = {"paired": False, "text_seen": False, "image_seen": False}
        self.assertEqual(PROBE.classify_deliveries([missing, missing]), "NEITHER_OBSERVED")
        self.assertEqual(
            PROBE.classify_deliveries([
                delivery(201, 2, 10, 20), delivery(202, 1, 3, 8),
            ]),
            "BOTH_REVERSED",
        )

    def test_turn_identity_is_read_from_actual_rpc_reply(self):
        reply = {"result": {"turn": {"id": "actual-returned-turn"}}}
        self.assertEqual(PROBE.turn_id_from_start_reply(reply), "actual-returned-turn")
        self.assertIsNone(PROBE.turn_id_from_start_reply({"result": {}}))

    def test_external_turn_identity_is_read_from_the_rpc_reply(self):
        reply = {"result": {"turn": {"id": "actual-returned-turn"}}}
        self.assertEqual(PROBE.turn_id_from_start_reply(reply), "actual-returned-turn")

    def test_missing_external_turn_identity_is_not_assumed(self):
        self.assertIsNone(PROBE.turn_id_from_start_reply({"result": {}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
