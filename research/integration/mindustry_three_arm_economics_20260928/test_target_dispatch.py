"""Host tests for the sequence-bound, non-sending pointer command compiler."""

import unittest
import sys
from pathlib import Path

from target_dispatch import DispatchStop, compile_pointer_click

LIVE = Path(__file__).resolve().parents[2] / "live_control"
sys.path.insert(0, str(LIVE))
from delivery_ledger_v2 import DeliveryLedger


def locator(sequence=7):
    return {"palette_point": [1008, 578], "target_point": [640, 410],
            "validated_sequence": sequence,
            "delivery_id": f"delivery:{sequence}",
            "authority": "locator only; explicit caller action still required"}


class TargetDispatchTests(unittest.TestCase):
    def test_compiles_one_palette_click_bound_to_the_visual_sequence(self):
        command = compile_pointer_click(locator(),
            {"sequence": 7, "runtime_ns": 100}, "A1", "palette_point")
        self.assertEqual(command["expected_sequence"], 7)
        self.assertEqual(command["valid_until_ns"], 5_000_000_100)
        self.assertEqual(command["id"], "A1-select-conveyor")
        self.assertEqual(sum(step["op"] == "pointer_click"
                             for step in command["steps"]), 1)
        self.assertEqual(command["authority"],
                         "compiled request only; not dispatched or admitted")

    def test_compiled_request_passes_the_live_submit_delivery_ledger(self):
        ledger = DeliveryLedger()
        item = ledger.prepare({"event": "observation", "sequence": 7,
                               "image": "observation-7.png"})
        ledger.flushed(item, 123, 100)
        current_locator = locator()
        current_locator["delivery_id"] = item["delivery_id"]
        command = compile_pointer_click(current_locator,
            {"sequence": 7, "runtime_ns": 100}, "A1", "target_point",
            protocol="interactive-v27")
        accepted = ledger.validate(command["decision_evidence"])
        self.assertEqual(accepted["source_delivery_id"], item["delivery_id"])
        self.assertEqual(accepted["observation_sequence"], command["expected_sequence"])
        self.assertEqual(accepted["producer"], "assistant")

    def test_mindustry_task_socket_dialect_needs_no_unavailable_delivery_id(self):
        current = locator()
        del current["delivery_id"]
        command = compile_pointer_click(current,
            {"sequence": 7, "runtime_ns": 100}, "A1", "target_point")
        self.assertNotIn("decision_evidence", command)
        self.assertEqual(command["expected_sequence"], 7)

    def test_generic_protocol_requires_flushed_delivery_identity(self):
        current = locator()
        del current["delivery_id"]
        with self.assertRaisesRegex(DispatchStop, "flushed observation"):
            compile_pointer_click(current,
                {"sequence": 7, "runtime_ns": 100}, "A1", "target_point",
                protocol="interactive-v27")

    def test_compiles_world_click_without_preview_settle(self):
        command = compile_pointer_click(locator(),
            {"sequence": 7, "runtime_ns": 100}, "B1", "target_point")
        self.assertEqual(command["steps"][0]["x"], 640)
        self.assertNotIn("settle", [step["op"] for step in command["steps"]])

    def test_sequence_advance_after_validation_refuses_before_dispatch(self):
        with self.assertRaisesRegex(DispatchStop, "sequence advanced"):
            compile_pointer_click(locator(),
                {"sequence": 8, "runtime_ns": 100}, "A1", "target_point")

    def test_malformed_or_non_authorizing_locator_refuses(self):
        forged = locator()
        forged["authority"] = "input authority granted"
        with self.assertRaisesRegex(DispatchStop, "non-authorizing"):
            compile_pointer_click(forged,
                {"sequence": 7, "runtime_ns": 100}, "A1", "target_point")

        missing_delivery = locator()
        del missing_delivery["delivery_id"]
        with self.assertRaisesRegex(DispatchStop, "flushed observation"):
            compile_pointer_click(missing_delivery,
                {"sequence": 7, "runtime_ns": 100}, "A1", "target_point",
                protocol="interactive-v27")

        with self.assertRaisesRegex(DispatchStop, "unknown preregistered"):
            compile_pointer_click(locator(),
                {"sequence": 7, "runtime_ns": 100}, "A4", "target_point")


if __name__ == "__main__":
    unittest.main()
