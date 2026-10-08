from argparse import Namespace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v28 as controller


class FakePlanner:
    def __init__(self):
        self.calls = []

    def begin_turn(self, prompt, **params):
        self.calls.append((prompt, params))
        return "handle"


class Map01ThreatFixtureV28Tests(unittest.TestCase):
    def test_session_command_requires_v7_fixture_load(self):
        args = Namespace(seed=990619, load_fixture_manifest=Path("fixture.json"))
        command = controller.session_command(args, Path("runtime"))
        self.assertIn("session_map01_v7.py", command[1])
        self.assertEqual(command[-2], "--load-fixture-manifest")
        self.assertEqual(command[-1], str(Path("fixture.json").resolve()))

    def test_command_suppresses_every_unused_capability(self):
        command = controller.app_server_command()
        for feature in controller.DISABLED_FEATURES:
            self.assertIn(feature, command)
        for name in controller.DISABLED_MCPS:
            self.assertIn(f"mcp_servers.{name}.enabled=false", command)

    def test_turn_keeps_temporal_image_schema_and_effect_memory(self):
        planner = FakePlanner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sheet.png"
            image.write_bytes(b"fixture")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                handle = controller.begin_model_turn(
                    planner, root, image, ["forward"], {"type": "object"})
        self.assertEqual(handle, "handle")
        prompt, params = planner.calls[0]
        self.assertIn('["forward"]', prompt)
        self.assertEqual(params["image_path"], r"C:\sheet.png")

    def test_semantic_action_validation_still_fails_closed(self):
        with self.assertRaises(ValueError):
            controller.validate_action({
                "state": "active", "commands": [], "contingencies": [], "next_cover": []})
        controller.validate_action({
            "state": "active", "commands": [{"action": "fire", "extent": "pulse"}],
            "contingencies": [], "next_cover": []})


if __name__ == "__main__":
    unittest.main()
