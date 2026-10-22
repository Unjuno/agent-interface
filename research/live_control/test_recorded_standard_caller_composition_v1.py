import json
import hashlib
import importlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class RecordedStandardCallerTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for the inert CLI")
    def test_preflight_and_integrated_model_call_are_both_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cli = root / "inert-cli.js"
            response = {
                "format": "plain-form-points-v1",
                "field": {"point_space": "source_observation_pixels",
                          "point": {"x": 10, "y": 20}},
                "submit": {"point_space": "source_observation_pixels",
                           "point": {"x": 30, "y": 40}},
            }
            events = [
                {"type": "thread.started", "thread_id": "inert-thread"},
                {"type": "item.completed", "item": {
                    "type": "agent_message", "text": json.dumps(response)}},
                {"type": "turn.completed", "usage": {
                    "input_tokens": 31, "output_tokens": 9}},
            ]
            cli.write_text(
                "if (process.argv.includes('--version')) { console.log('inert-1'); } "
                "else { const rows=" + json.dumps(events) + "; let input=''; "
                "process.stdin.setEncoding('utf8'); "
                "process.stdin.on('data', c => input += c); "
                "process.stdin.on('end', () => process.stdout.write(" 
                "rows.map(r => JSON.stringify(r)).join(String.fromCharCode(10)) + "
                "String.fromCharCode(10))); }\n",
                encoding="utf-8")
            node = shutil.which("node")
            wrapper = str(HERE / "recorded_target_handle_model_runner_v1.py")
            env = dict(os.environ)
            env["AGENT_INTERFACE_MODEL_RUNNER"] = wrapper
            schema_preflight = __import__("schema_preflight_v1")
            model = __import__("integrated_efficiency_model_v1")
            schema_path = HERE / "plain_form_points_schema_v1.json"
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.png"
            image.write_bytes(b"inert observation bytes")

            with patch.dict(os.environ, {"AGENT_INTERFACE_MODEL_RUNNER": wrapper}):
                schema_preflight = importlib.reload(schema_preflight)
                model = importlib.reload(model)
            self.assertEqual(schema_preflight.RUNNER, Path(wrapper))
            self.assertEqual(model.RUNNER, Path(wrapper))

            for module in (schema_preflight, model):
                module.WINDOWS_PYTHON = Path(sys.executable)
                module.windows_path = lambda value: str(Path(value).resolve())
            schema_preflight.NODE_WSL = Path(node)
            schema_preflight.NODE_ARG = node
            schema_preflight.CLI_WSL = cli
            schema_preflight.CLI_ARG = str(cli)
            model.NODE = node
            model.CLI = str(cli)

            preflight_result = schema_preflight.preflight(
                schema_path, root / "preflight-cache", root / "preflight-result", workspace)
            self.assertEqual(preflight_result["endpoint_status"], "ENDPOINT_COMPATIBLE")
            self.assertEqual(preflight_result["usage"]["input_tokens"], 31)
            preflight_output = root / "preflight-result" / "model-call"
            preflight_ref = json.loads((preflight_output / "attempt-ledger-ref.json")
                                       .read_text(encoding="utf-8"))
            preflight_ledger = (preflight_output /
                                preflight_ref["ledger_relative_path"]).resolve()
            preflight_rows = [json.loads(line) for line in
                              (preflight_ledger / "attempts.jsonl").read_text(
                                  encoding="utf-8").splitlines()]
            preflight_request = json.loads((preflight_ledger /
                preflight_rows[0]["request_ref"]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(preflight_request["mode"], "handle")
            self.assertIsNone(preflight_request["image_base64"])

            result = model.call(root / "comparison-call", "fill the form", image,
                                "plain", workspace)
            self.assertEqual(result["grounding"]["field_point"], [10, 20])
            model_output = root / "comparison-call" / "model"
            model_ref = json.loads((model_output / "attempt-ledger-ref.json")
                                   .read_text(encoding="utf-8"))
            model_ledger = (model_output / model_ref["ledger_relative_path"]).resolve()
            model_rows = [json.loads(line) for line in
                          (model_ledger / "attempts.jsonl").read_text(
                              encoding="utf-8").splitlines()]
            model_request = json.loads((model_ledger /
                model_rows[0]["request_ref"]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(model_request["mode"], "coordinate")
            self.assertEqual(model_request["image_sha256"],
                             hashlib.sha256(image.read_bytes()).hexdigest())
            self.assertEqual(model_ref["usage"]["input_tokens"], 31)


if __name__ == "__main__":
    unittest.main()
