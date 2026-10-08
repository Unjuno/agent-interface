import json
import unittest
from pathlib import Path

from frontier_profile import DISABLED_FEATURES, build_args

HERE = Path(__file__).resolve().parent


class FrontierProfileTests(unittest.TestCase):
    def test_every_capability_feature_is_disabled_in_cli_argv(self):
        args = build_args("images/c01.png", "decision.schema.json")
        disabled = [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == "--disable"]
        self.assertEqual(tuple(disabled), DISABLED_FEATURES)
        self.assertIn("--ignore-user-config", args)
        self.assertIn("--ignore-rules", args)
        self.assertIn("--ephemeral", args)
        self.assertIn("--sandbox", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertEqual(args[-1], "-")

    def test_model_image_schema_and_low_effort_are_bound(self):
        args = build_args("case.png", "schema.json")
        self.assertEqual(args[args.index("--model") + 1], "gpt-6-astra")
        self.assertEqual(args[args.index("--image") + 1], "case.png")
        self.assertEqual(args[args.index("--output-schema") + 1], "schema.json")
        self.assertEqual(args[args.index("-c") + 1], 'model_reasoning_effort="low"')

    def test_rejects_missing_run_inputs(self):
        for args in (("", "schema.json"), ("case.png", ""), ("case.png", "schema.json", "")):
            with self.assertRaisesRegex(ValueError, "required"):
                build_args(*args)

    def test_json_schema_is_closed_and_matches_supported_decisions(self):
        schema = json.loads((HERE / "decision.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], ["decision", "target", "container", "state", "reason"])
        self.assertEqual(
            set(schema["properties"]["decision"]["enum"]),
            {"TARGET", "STATE", "NO_ACTION", "YIELD"},
        )
        self.assertEqual(schema["properties"]["state"]["type"], ["string", "null"])
        self.assertNotIn("oneOf", schema)
        self.assertNotIn("anyOf", schema)


if __name__ == "__main__":
    unittest.main()
