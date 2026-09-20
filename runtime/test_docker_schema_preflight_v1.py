import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from runtime.docker_schema_preflight_v1 import main, validate_model_response


class DockerSchemaPreflightAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.events = self.root / "events.jsonl"
        self.schema = self.root / "schema.json"
        self.schema.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["answer"],
            "additionalProperties": False,
            "properties": {"answer": {"type": "string", "const": "ok"}},
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_events(self, text, *, item_type="agent_message", add_other_item=False):
        events = [
            {"type": "turn.completed", "usage": {"input_tokens": 12,
                                                       "output_tokens": 3}},
            {"type": "item.completed", "item": {"type": item_type,
                                                       "text": text}},
        ]
        if add_other_item:
            events.insert(1, {"type": "item.completed",
                              "item": {"type": "reasoning", "text": "private"}})
        self.events.write_text("".join(json.dumps(row) + "\n" for row in events),
                               encoding="utf-8")

    def test_pass_requires_one_agent_message_matching_schema(self):
        self.write_events('{"answer":"ok"}', add_other_item=True)
        result = validate_model_response(self.events, self.schema)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["messages"], 1)
        self.assertEqual(result["usage"]["input_tokens"], 12)
        self.assertEqual(len(result["response_sha256"]), 64)

    def test_valid_json_that_violates_schema_is_stop(self):
        self.write_events('{"answer":"wrong","private":"do-not-copy"}')
        result = validate_model_response(self.events, self.schema)
        self.assertEqual(result["status"], "STOP_SCHEMA_OUTPUT_INVALID")
        self.assertNotIn("do-not-copy", json.dumps(result))
        self.assertIn("schema_keyword", result)

    def test_current_integrated_efficiency_schemas_accept_valid_outputs(self):
        live_control = Path(__file__).resolve().parents[1] / "research" / "live_control"
        method = {
            "first_action": "enter_exact_token",
            "continue_when": "field_pixels_changed_and_submit_revalidated",
            "second_action": "activate_submit",
            "complete_when": "submission_pixels_changed_then_independent_score",
        }
        compiled = {
            "format": "compiled-form-grounding-v1",
            "field": {"point_space": "source_observation_pixels",
                      "point": {"x": 10, "y": 20},
                      "motion_model": "surface_origin_translation"},
            "submit": {"point_space": "source_observation_pixels",
                       "point": {"x": 30, "y": 40},
                       "motion_model": "surface_origin_translation"},
            "method": method,
        }
        plain = {
            "format": "plain-form-points-v1",
            "field": {"point_space": "source_observation_pixels",
                      "point": {"x": 10, "y": 20}},
            "submit": {"point_space": "source_observation_pixels",
                       "point": {"x": 30, "y": 40}},
        }
        for schema_name, value in (
                ("compiled_form_grounding_schema_v1.json", compiled),
                ("plain_form_points_schema_v1.json", plain)):
            with self.subTest(schema=schema_name):
                schema_path = live_control / schema_name
                self.assertTrue(schema_path.is_file())
                self.write_events(json.dumps(value))
                result = validate_model_response(self.events, schema_path)
                self.assertEqual(result["status"], "PASS")

    def test_non_json_agent_message_is_stop(self):
        self.write_events("not json")
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_INVALID_JSON_OUTPUT")

    def test_non_agent_item_is_not_counted_as_model_answer(self):
        self.write_events('{"answer":"ok"}', item_type="reasoning")
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_MALFORMED_MODEL_RESPONSE")

    def test_invalid_schema_is_stop(self):
        self.schema.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "not-a-json-schema-type",
        }), encoding="utf-8")
        self.write_events('{"answer":"ok"}')
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_INVALID_OUTPUT_SCHEMA")

    def test_remote_schema_reference_is_rejected_without_resolution(self):
        self.schema.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": "https://example.invalid/schema",
        }), encoding="utf-8")
        self.write_events('{"answer":"ok"}')
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_REMOTE_SCHEMA_REFERENCE")

    def test_local_reference_must_resolve(self):
        self.schema.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": "#/$defs/missing",
        }), encoding="utf-8")
        self.write_events('{"answer":"ok"}')
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_INVALID_OUTPUT_SCHEMA")

    def test_schema_dialect_must_be_declared(self):
        self.schema.write_text('{"type":"object"}', encoding="utf-8")
        self.write_events('{"answer":"ok"}')
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_SCHEMA_DIALECT_UNDECLARED")

    def test_malformed_event_stream_is_stop(self):
        self.events.write_text('{broken json\n', encoding="utf-8")
        self.assertEqual(validate_model_response(self.events, self.schema)["status"],
                         "STOP_MALFORMED_MODEL_RESPONSE")

    def run_preflight(self, response_text):
        output = self.root / "output"
        arguments = ["docker_schema_preflight_v1.py", "--runner", str(self.root / "runner.py"),
                     "--prompt", str(self.root / "prompt.txt"), "--working", str(self.root),
                     "--output", str(output), "--instructions", str(self.root / "instructions.txt"),
                     "--schema", str(self.schema), "--ipc", str(self.root / "ipc")]

        def fake_runner(command, **_kwargs):
            runner_output = Path(command[6])
            runner_output.mkdir(parents=True)
            (runner_output / "process.json").write_text("{}", encoding="utf-8")
            (runner_output / "events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in (
                {"type": "turn.completed", "usage": {"input_tokens": 5}},
                {"type": "item.completed", "item": {"type": "agent_message",
                                                         "text": response_text}},
            )), encoding="utf-8")
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with patch.object(sys, "argv", arguments), \
                patch("runtime.docker_schema_preflight_v1.subprocess.run", side_effect=fake_runner):
            return_code = main()
        return return_code, json.loads((output / "report.json").read_text(encoding="utf-8"))

    def test_main_passes_only_after_schema_validation(self):
        return_code, report = self.run_preflight('{"answer":"ok"}')
        self.assertEqual(return_code, 0)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["schema_valid"])

    def test_main_returns_nonzero_and_safe_report_for_schema_mismatch(self):
        return_code, report = self.run_preflight('{"answer":"secret-value"}')
        self.assertEqual(return_code, 1)
        self.assertEqual(report["status"], "STOP_SCHEMA_OUTPUT_INVALID")
        self.assertNotIn("secret-value", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
