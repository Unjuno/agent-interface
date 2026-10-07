import json
from pathlib import Path
import tempfile
import unittest

from research.live_control.codex_app_server_command_v1 import (
    DISABLED_FEATURES, DISABLED_MCPS, command,
)
from research.live_control.integrated_efficiency_app_server_model_v1 import (
    PersistentGroundingModel, per_turn_usage,
)


def raw(field_x, submit_x):
    target = lambda x, y: {
        "point_space": "source_observation_pixels",
        "point": {"x": x, "y": y},
        "motion_model": "surface_origin_translation",
    }
    return {
        "format": "compiled-form-grounding-v1",
        "field": target(field_x, 200),
        "submit": target(submit_x, 300),
        "method": {
            "first_action": "enter_exact_token",
            "continue_when": "field_pixels_changed_and_submit_revalidated",
            "second_action": "activate_submit",
            "complete_when": "submission_pixels_changed_then_independent_score",
        },
    }


class FakeClient:
    def __init__(self, answers, usages):
        self.answers = list(answers)
        self.usages = list(usages)
        self.turn = 0
        self.thread_starts = 0
        self.turn_threads = []

    def start_thread(self, **_params):
        self.thread_starts += 1
        return {"thread": {"id": "thread-1"}}

    def start_turn(self, thread_id, _inputs, **_params):
        self.turn += 1
        self.turn_threads.append(thread_id)
        return {"turn": {"id": f"turn-{self.turn}"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        answer = self.answers[self.turn - 1]
        return {"threadId": thread_id, "turn": {
            "id": turn_id, "status": "completed",
            "items": [{"type": "agentMessage", "text": json.dumps(answer)}]}}

    def latest_turn_usage(self, _thread_id, _turn_id):
        return self.usages[self.turn - 1]


def usage(input_tokens, cached):
    return {"last": {"inputTokens": input_tokens, "cachedInputTokens": cached,
                     "cacheWriteInputTokens": 0, "outputTokens": 20,
                     "reasoningOutputTokens": 5}}


class PersistentIntegratedModelTests(unittest.TestCase):
    def test_minimal_command_is_explicit(self):
        value = command("node", "cli.js")
        self.assertEqual(value[:4], ["node", "cli.js", "app-server", "--stdio"])
        self.assertTrue(all(feature in value for feature in DISABLED_FEATURES))
        self.assertTrue(all(f"mcp_servers.{name}.enabled=false" in value
                            for name in DISABLED_MCPS))
        self.assertNotIn("mcp_servers={}", value)

    def test_two_calls_keep_thread_and_return_distinct_call_ids_and_last_usage(self):
        client = FakeClient([raw(100, 500), raw(110, 510)],
                            [usage(8000, 0), usage(8200, 7000)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "image.png"
            image.write_bytes(b"fixture")
            model = PersistentGroundingModel(
                root / "session", workspace, node="node", cli="cli",
                client=client, path_converter=lambda path: "WIN:" + str(path))
            first = model.call(root / "call-1", "first", image, "compiled", workspace)
            second = model.call(root / "call-2", "second", image, "compiled", workspace)
        self.assertEqual(client.thread_starts, 1)
        self.assertEqual(client.turn_threads, ["thread-1", "thread-1"])
        self.assertEqual([first["call_id"], second["call_id"]], ["turn-1", "turn-2"])
        self.assertEqual(first["thread_id"], second["thread_id"])
        self.assertEqual(second["usage"], {
            "input_tokens": 8200, "cached_input_tokens": 7000,
            "cache_write_input_tokens": 0, "output_tokens": 20,
            "reasoning_output_tokens": 5})
        self.assertEqual(second["grounding"]["field_point"], [110, 200])

    def test_usage_missing_stays_unknown_and_bad_shape_is_rejected(self):
        self.assertIsNone(per_turn_usage(None))
        with self.assertRaises(ValueError):
            per_turn_usage({"total": {}})
        with self.assertRaises(ValueError):
            per_turn_usage(usage(-1, 0))

    def test_contract_or_workspace_change_is_rejected_before_turn(self):
        client = FakeClient([raw(100, 500)], [usage(1, 0)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "image.png"
            image.write_bytes(b"fixture")
            model = PersistentGroundingModel(
                root / "session", workspace, node="node", cli="cli",
                client=client, path_converter=str)
            with self.assertRaises(ValueError):
                model.call(root / "wrong-contract", "x", image, "plain", workspace)
            other = root / "other"
            other.mkdir()
            with self.assertRaises(ValueError):
                model.call(root / "wrong-workspace", "x", image, "compiled", other)
        self.assertEqual(client.turn, 0)


if __name__ == "__main__":
    unittest.main()
