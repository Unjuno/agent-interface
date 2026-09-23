import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v26 as controller


class FakePlanner:
    def __init__(self):
        self.calls = []

    def begin_turn(self, prompt, **params):
        self.calls.append((prompt, params))
        return "handle"


class Map01PersistentPlannerV26Tests(unittest.TestCase):
    def test_command_suppresses_every_preregistered_unused_capability(self):
        command = controller.app_server_command()
        self.assertEqual(command[:3], [controller.NODE, controller.CLI, "app-server"])
        for feature in controller.DISABLED_FEATURES:
            self.assertIn(feature, command)
        for name in controller.DISABLED_MCPS:
            self.assertIn(f"mcp_servers.{name}.enabled=false", command)
        self.assertNotIn("mcp_servers={}", command)

    def test_turn_uses_temporal_image_schema_and_effect_memory(self):
        planner = FakePlanner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sheet.png"
            image.write_bytes(b"fixture")
            schema = {"type": "object"}
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                handle = controller.begin_model_turn(
                    planner, root, image, ["forward", "use"], schema)
            self.assertEqual(handle, "handle")
            prompt, params = planner.calls[0]
            self.assertIn('["forward","use"]', prompt)
            self.assertEqual(params, {
                "output_schema": schema, "image_path": r"C:\sheet.png"})
            self.assertEqual((root / "prompt.txt").read_text(), prompt)

    def test_semantic_action_checks_remain_in_front_of_input_compilation(self):
        with self.assertRaises(ValueError):
            controller.validate_action({
                "state": "active", "commands": [], "contingencies": [], "next_cover": []})
        with self.assertRaises(ValueError):
            controller.validate_action({
                "state": "dead", "commands": [{"action": "fire", "extent": "pulse"}],
                "contingencies": [], "next_cover": []})
        with self.assertRaises(ValueError):
            controller.validate_action({
                "state": "active", "commands": [{"action": "use", "extent": "pulse"}],
                "contingencies": [
                    {"after_command": 0}, {"after_command": 0}], "next_cover": []})
        controller.validate_action({
            "state": "active", "commands": [{"action": "use", "extent": "pulse"}],
            "contingencies": [{"after_command": 0}], "next_cover": []})


if __name__ == "__main__":
    unittest.main()
