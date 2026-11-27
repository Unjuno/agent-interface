import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import recorded_target_handle_model_runner_v1 as wrapper
from provider_attempt_recorder import ProviderAttemptRecorder


class RecordedTargetHandleRunnerTests(unittest.TestCase):
    def test_success_records_preflight_style_and_image_style_runner_requests(self):
        for mode, image_bytes in (("handle", None), ("coordinate", b"synthetic-image")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "call-output"
                prompt = root / "prompt.txt"
                schema = root / "schema.json"
                instructions = root / "instructions.txt"
                working = root / "workspace"
                prompt.write_bytes(b"schema probe prompt")
                schema.write_bytes(b'{"type":"object"}')
                instructions.write_bytes(b"exact responder instruction")
                working.mkdir()
                image = "-"
                if image_bytes is not None:
                    image_path = root / "image.png"
                    image_path.write_bytes(image_bytes)
                    image = str(image_path)
                argv = ["node", "codex.js", str(prompt), str(working), str(output),
                        mode, image, str(instructions), str(schema)]
                events = (b'{"type":"thread.started","thread_id":"t"}\n'
                          b'{"type":"turn.completed","usage":{"input_tokens":13,'
                          b'"output_tokens":4}}\n')
                calls = []

                def delegate(args):
                    calls.append(args)
                    output.mkdir()
                    (output / "events.jsonl").write_bytes(events)
                    (output / "process.json").write_text('{"exit_code":0}')
                    return subprocess.CompletedProcess(args, 0, b"runner-out", b"runner-err")

                code, stdout, stderr = wrapper.run_attempt(argv, delegate=delegate)
                self.assertEqual((code, stdout, stderr), (0, b"runner-out", b"runner-err"))
                self.assertEqual(len(calls), 1)
                ledger_root = output.parent / "call-output.attempt-ledger"
                rows = [json.loads(line) for line in
                        (ledger_root / "attempts.jsonl").read_text().splitlines()]
                self.assertEqual([row["event"] for row in rows],
                                 ["model_attempt_started", "model_attempt_finished"])
                self.assertEqual(rows[1]["status"], "completed")
                self.assertEqual(rows[1]["usage"]["input_tokens"], 13)
                request_ref = rows[0]["request_ref"]
                request = json.loads((ledger_root / request_ref["path"]).read_bytes())
                self.assertEqual(base64.b64decode(request["prompt_base64"]),
                                 b"schema probe prompt")
                self.assertEqual(base64.b64decode(request["schema_base64"]),
                                 b'{"type":"object"}')
                self.assertEqual(base64.b64decode(request["instructions_base64"]),
                                 b"exact responder instruction")
                self.assertEqual(request["image_base64"],
                                 None if image_bytes is None else
                                 base64.b64encode(image_bytes).decode())
                self.assertEqual(request["mode"], mode)
                response = json.loads((ledger_root / rows[1]["response_ref"]["path"])
                                      .read_bytes())
                response_files = {item["name"]: base64.b64decode(item["bytes_base64"])
                                  for item in response["files"]}
                self.assertEqual(response_files["events.jsonl"], events)
                reference = json.loads((output / "attempt-ledger-ref.json")
                                       .read_text(encoding="utf-8"))
                self.assertEqual(reference["status"], "completed")
                self.assertTrue(reference["journal_complete"])
                self.assertEqual(reference["journal_sha256"], hashlib.sha256(
                    (ledger_root / "attempts.jsonl").read_bytes()).hexdigest())
                self.assertTrue(ProviderAttemptRecorder(ledger_root).reconcile()["complete"])

    def test_timeout_is_retained_with_partial_events_and_no_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "timed-out"
            prompt = root / "prompt.txt"
            instructions = root / "instructions.txt"
            schema = root / "schema.json"
            working = root / "workspace"
            prompt.write_bytes(b"prompt")
            instructions.write_bytes(b"instructions")
            schema.write_bytes(b"{}")
            working.mkdir()
            partial = b'{"type":"thread.started","thread_id":"partial"}\n'
            calls = []

            def delegate(_args):
                calls.append(True)
                output.mkdir()
                (output / "events.jsonl").write_bytes(partial)
                raise subprocess.TimeoutExpired(["fake-runner"], 90,
                                                output=b"partial-out",
                                                stderr=b"partial-err")

            code, stdout, stderr = wrapper.run_attempt(
                ["node", "cli", str(prompt), str(working), str(output), "handle", "-",
                 str(instructions), str(schema)], delegate=delegate)
            self.assertEqual((code, stdout, stderr), (124, b"partial-out", b"partial-err"))
            self.assertEqual(len(calls), 1)
            ledger_root = output.parent / "timed-out.attempt-ledger"
            rows = [json.loads(line) for line in
                    (ledger_root / "attempts.jsonl").read_text().splitlines()]
            self.assertEqual(rows[1]["status"], "timeout")
            self.assertEqual(rows[1]["usage"]["status"], "unavailable")
            response = json.loads((ledger_root / rows[1]["response_ref"]["path"])
                                  .read_bytes())
            response_files = {item["name"]: base64.b64decode(item["bytes_base64"])
                              for item in response["files"]}
            self.assertEqual(response_files["events.jsonl"], partial)
            self.assertEqual(base64.b64decode(response["stdout_base64"]), b"partial-out")
            reference = json.loads((output / "attempt-ledger-ref.json")
                                   .read_text(encoding="utf-8"))
            self.assertEqual(reference["status"], "timeout")
            self.assertTrue(reference["journal_complete"])
            self.assertTrue(ProviderAttemptRecorder(ledger_root).reconcile()["complete"])

    def test_both_existing_runner_call_sites_accept_explicit_wrapper_path(self):
        env = dict(os.environ)
        env["AGENT_INTERFACE_MODEL_RUNNER"] = str(HERE / "recorded_target_handle_model_runner_v1.py")
        completed = subprocess.run(
            [sys.executable, "-c",
             "import schema_preflight_v1 as p, integrated_efficiency_model_v1 as m; "
             "assert p.RUNNER == m.RUNNER; "
             "assert p.RUNNER.name == 'recorded_target_handle_model_runner_v1.py'"],
            cwd=HERE, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the inert CLI fixture")
    def test_real_target_runner_path_records_an_inert_cli_response(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prompt = root / "prompt.txt"
            image = root / "observation.png"
            instructions = root / "instructions.txt"
            schema = root / "schema.json"
            workspace = root / "workspace"
            output = root / "model-call"
            prompt.write_text("synthetic prompt", encoding="utf-8")
            image.write_bytes(b"synthetic image bytes")
            instructions.write_text("synthetic instructions", encoding="utf-8")
            schema.write_text('{"type":"object"}', encoding="utf-8")
            workspace.mkdir()
            cli = root / "fake-cli.js"
            rows = [
                {"type": "thread.started", "thread_id": "thread-inert"},
                {"type": "item.completed", "item": {
                    "type": "agent_message", "text": "{}"}},
                {"type": "turn.completed", "usage": {
                    "input_tokens": 19, "output_tokens": 5}},
            ]
            payload = json.dumps(rows, separators=(",", ":"))
            script = (f"const rows={payload}; let input=''; "
                      "process.stdin.setEncoding('utf8'); "
                      "process.stdin.on('data', chunk => input += chunk); "
                      "process.stdin.on('end', () => process.stdout.write("
                      "rows.map(row => JSON.stringify(row)).join(String.fromCharCode(10)) + "
                      "String.fromCharCode(10)));\n")
            cli.write_text(script, encoding="utf-8")

            code, stdout, _stderr = wrapper.run_attempt([
                shutil.which("node"), str(cli), str(prompt), str(workspace),
                str(output), "coordinate", str(image), str(instructions), str(schema),
            ])
            self.assertEqual(code, 0, stdout)
            process = json.loads((output / "process.json").read_text(encoding="utf-8"))
            self.assertEqual(process["exit_code"], 0)
            events = (output / "events.jsonl").read_bytes()
            self.assertIn(b'"thread_id":"thread-inert"', events)
            reference = json.loads((output / "attempt-ledger-ref.json")
                                   .read_text(encoding="utf-8"))
            self.assertEqual(reference["status"], "completed")
            self.assertTrue(reference["journal_complete"])
            ledger_root = (output / reference["ledger_relative_path"]).resolve()
            journal = (ledger_root / "attempts.jsonl").read_bytes()
            self.assertEqual(hashlib.sha256(journal).hexdigest(),
                             reference["journal_sha256"])
            self.assertTrue(ProviderAttemptRecorder(ledger_root).reconcile()["complete"])

    def test_success_exit_without_exactly_one_terminal_event_is_malformed(self):
        for events in (
            b'{"type":"thread.started","thread_id":"missing-terminal"}\n',
            b'{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}\n'
            b'{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}\n',
        ):
            with self.subTest(events=events), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "malformed"
                prompt = root / "prompt.txt"
                schema = root / "schema.json"
                instructions = root / "instructions.txt"
                working = root / "workspace"
                prompt.write_bytes(b"prompt")
                schema.write_bytes(b"{}")
                instructions.write_bytes(b"instructions")
                working.mkdir()

                def delegate(args):
                    output.mkdir()
                    (output / "events.jsonl").write_bytes(events)
                    return subprocess.CompletedProcess(args, 0, b"", b"")

                code, _stdout, _stderr = wrapper.run_attempt(
                    ["node", "cli", str(prompt), str(working), str(output), "handle",
                     "-", str(instructions), str(schema)], delegate=delegate)
                self.assertEqual(code, 1)
                ledger_root = output.parent / "malformed.attempt-ledger"
                rows = [json.loads(line) for line in
                        (ledger_root / "attempts.jsonl").read_text().splitlines()]
                self.assertEqual(rows[1]["status"], "malformed")
                self.assertEqual(rows[1]["usage"]["status"], "unavailable")
                reference = json.loads((output / "attempt-ledger-ref.json")
                                       .read_text(encoding="utf-8"))
                self.assertEqual(reference["status"], "malformed")
                self.assertTrue(reference["journal_complete"])


if __name__ == "__main__":
    unittest.main()
