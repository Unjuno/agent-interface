"""Host tests for the sequence-bound, non-sending pointer command compiler."""

import unittest

from target_dispatch import DispatchStop, compile_pointer_click


def locator(sequence=7):
    return {"palette_point": [1008, 578], "target_point": [640, 410],
            "validated_sequence": sequence,
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

        with self.assertRaisesRegex(DispatchStop, "unknown preregistered"):
            compile_pointer_click(locator(),
                {"sequence": 7, "runtime_ns": 100}, "A4", "target_point")


if __name__ == "__main__":
    unittest.main()
