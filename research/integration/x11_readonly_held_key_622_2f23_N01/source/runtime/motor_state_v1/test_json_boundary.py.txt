"""Decoded JSON must retain its declared shape at the MotorState boundary."""
from __future__ import annotations

import copy
from types import MappingProxyType
import unittest

from .adapter import validate
from .dispatch_bridge import bridge_dispatch_result
from .test_adapter import base
from .test_dispatch_bridge import context


class MotorStateJsonBoundaryTests(unittest.TestCase):
    def test_adapter_enum_values_refuse_wrong_json_types(self):
        for field, reason in (("input_ack", "input_ack"),
                              ("release", "release"),
                              ("uncertainty", "uncertainty")):
            for value in (None, False, 0, 1.0, [], {}, ["ACKED"]):
                with self.subTest(field=field, value=value):
                    row = base()
                    if field == "uncertainty":
                        row[field] = value
                    else:
                        row[field]["status"] = value
                    snapshot = copy.deepcopy(row)
                    self.assertEqual(validate(row), (False, reason))
                    self.assertEqual(row, snapshot)

    def test_dispatch_status_refuses_wrong_json_types(self):
        for value in (None, False, 0, 1.0, [], {}, ["accepted"]):
            with self.subTest(value=value):
                row, report = bridge_dispatch_result({"status": value}, context())
                self.assertIsNone(row)
                self.assertIs(report["accepted"], False)
                self.assertEqual(report["reason"], "status")

    def test_context_containers_are_checked_before_conversion(self):
        wrong = {
            "events": (None, False, 0, 1.0, "", {}, {"type": "RELEASE_TRANSITION"}),
            "held_keys": (None, False, 0, 1.0, "", {}, {"key": "CTRL"}),
            "held_buttons": (None, False, 0, 1.0, "", {}, {"button": 1}),
            "commanded_pointer": (None, False, 0, 1.0, "", [], [["x", 1]]),
            "input_ack": (None, False, 0, 1.0, "", [], [["id", "ack1"], ["status", "ACKED"]]),
        }
        for field, values in wrong.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    original = context(**{field: value})
                    snapshot = copy.deepcopy(original)
                    row, report = bridge_dispatch_result({"status": "accepted"}, original)
                    self.assertIsNone(row)
                    self.assertIs(report["accepted"], False)
                    self.assertEqual(report["reason"], "context_" + field)
                    self.assertEqual(original, snapshot)

    def test_nested_enum_types_return_validation_reports(self):
        for value in ([], {}, ["ACKED"]):
            for field in ("input_ack", "release", "uncertainty"):
                with self.subTest(field=field, value=value):
                    result = {"status": "accepted"}
                    supplied = context()
                    if field == "release":
                        result["release"] = {"status": value, "retained": False}
                    elif field == "input_ack":
                        supplied[field]["status"] = value
                    else:
                        supplied[field] = value
                    row, report = bridge_dispatch_result(result, supplied)
                    self.assertIsNone(row)
                    self.assertIs(report["accepted"], False)
                    self.assertEqual(report["validation"], field)

    def test_optional_defaults_remain_uncertain(self):
        supplied = {key: context()[key] for key in (
            "state_id", "owner_id", "owner_revision", "observation_id",
            "surface_id", "coordinate_frame")}
        row, report = bridge_dispatch_result({"status": "accepted"}, supplied)
        self.assertIs(report["accepted"], True)
        self.assertEqual(row["uncertainty"], "OS_UNCONFIRMED")
        self.assertIsNone(row["observed_pointer"])
        self.assertEqual(row["input_ack"], {"id": "unknown", "status": "UNKNOWN"})

    def test_valid_mapping_inputs_and_list_copies_are_preserved(self):
        supplied = context(
            commanded_pointer=MappingProxyType({"x": 1}),
            input_ack=MappingProxyType({"id": "ack1", "status": "ACKED"}),
            held_keys=["CTRL"], held_buttons=[1],
            events=[{"type": "OBSERVED"}])
        row, report = bridge_dispatch_result(
            MappingProxyType({"status": "accepted"}), MappingProxyType(supplied))
        self.assertIs(report["accepted"], True)
        self.assertEqual(validate(row), (True, "ok"))
        for field in ("events", "held_keys", "held_buttons", "commanded_pointer", "input_ack"):
            self.assertEqual(row[field], supplied[field])
            self.assertIsNot(row[field], supplied[field])

    def test_valid_release_and_confirmation_rules_remain(self):
        row, report = bridge_dispatch_result(
            {"status": "accepted", "release": {"status": "VERIFIED_EMPTY", "retained": True}},
            context(events=[{"type": "RELEASE_TRANSITION"}]))
        self.assertIs(report["accepted"], True)
        self.assertEqual(row["uncertainty"], "NONE")
        row, report = bridge_dispatch_result(
            {"status": "accepted"}, context(input_ack={"id": "ack1", "status": "PENDING"}))
        self.assertIsNone(row)
        self.assertEqual(report["validation"], "implicit_confirmation")

    def test_invalid_context_never_becomes_accepted_for_other_statuses(self):
        for status in ("rejected", "failed", "released"):
            with self.subTest(status=status):
                result = {"status": status, "release": {"status": "FAILED", "retained": True}}
                supplied = context(events={})
                snapshot = copy.deepcopy((result, supplied))
                row, report = bridge_dispatch_result(result, supplied)
                self.assertIsNone(row)
                self.assertIs(report["accepted"], False)
                self.assertEqual(report["reason"], "context_events")
                self.assertEqual(report["release"], result["release"])
                self.assertEqual((result, supplied), snapshot)


if __name__ == "__main__":
    unittest.main()
