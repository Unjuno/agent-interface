import copy
import json
import tempfile
import unittest
from pathlib import Path

from openttd_effect_model_v1 import parse, validate


class TestOpenTTDEffectDecision(unittest.TestCase):
    def test_status_action_pairs_are_closed(self):
        pairs = {
            "observed": "advance_without_repeat",
            "uncertain": "inspect_without_mutation",
            "contradicted": "recover_without_repeat",
        }
        for status, action in pairs.items():
            with self.subTest(status=status):
                value = {"format": "openttd-effect-decision-v1", "status": status,
                         "next_action": action, "memory_use": "supporting"}
                self.assertEqual(validate(value), value)

    def test_repeating_completed_drag_is_not_representable(self):
        value = {"format": "openttd-effect-decision-v1", "status": "observed",
                 "next_action": "repeat_drag", "memory_use": "supporting"}
        with self.assertRaisesRegex(ValueError, "conflict"):
            validate(value)

    def test_extra_field_fails_closed(self):
        value = {"format": "openttd-effect-decision-v1", "status": "observed",
                 "next_action": "advance_without_repeat", "memory_use": "none", "x": 1}
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate(value)

    def test_parse_requires_one_complete_turn_and_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            decision = {"format": "openttd-effect-decision-v1", "status": "observed",
                        "next_action": "advance_without_repeat", "memory_use": "none"}
            events = [
                {"type": "thread.started", "thread_id": "call-1"},
                {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(decision)}},
                {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 2,
                    "cache_write_input_tokens": 0, "output_tokens": 4, "reasoning_output_tokens": 1}},
            ]
            (root / "events.jsonl").write_text("\n".join(map(json.dumps, events)) + "\n", encoding="utf-8")
            (root / "process.json").write_text(json.dumps({"exit_code": 0,
                "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                "visible_images_submitted": 1, "started_ns": 2, "exited_ns": 5}), encoding="utf-8")
            parsed = parse(root)
            self.assertEqual(parsed["decision"], decision)
            self.assertEqual(parsed["usage"]["input_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
