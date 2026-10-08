"""Exercise the real host IPC runner and broker against an inert fake CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

LIVE = Path(__file__).parent
ROOT = LIVE.parents[1]
sys.path.insert(0, str(LIVE))
import docker_model_call_backend_v1 as backend


class DockerHostIpcPathResolutionTests(unittest.TestCase):
    def test_inert_runner_and_host_broker_resolve_shared_repo_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            host_repo = base / "broker-repo"
            host_repo.mkdir()
            ipc = base / "ipc"
            ipc.mkdir()
            workspace = base / "workspace"
            workspace.mkdir()
            out = base / "out"
            out.mkdir()
            runner = LIVE / "container_host_model_ipc_runner_v1.py"
            schema = base / "schema.json"
            schema.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object", "properties": {"compatible": {"const": True}},
                "required": ["compatible"], "additionalProperties": False,
            }), encoding="utf-8")
            instructions = base / "instructions.txt"
            instructions.write_text("fixed test instruction", encoding="utf-8")
            prompt = out / "prompt.txt"
            prompt.write_text("return compatible true", encoding="utf-8")
            fake_cli = base / "fake-codex"
            fake_cli.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                "args=sys.argv[1:]\n"
                "schema=pathlib.Path(args[args.index('--output-schema')+1])\n"
                "work=pathlib.Path(args[args.index('-C')+1])\n"
                "assert schema.is_file() and work.is_dir()\n"
                "assert json.loads(schema.read_text())['required']==['compatible']\n"
                "events=[{'type':'thread.started','thread_id':'inert-call'},"
                "{'type':'item.completed','item':{'type':'agent_message',"
                "'text':'{\\\"compatible\\\": true}'}},"
                "{'type':'turn.completed','usage':{'input_tokens':5,'output_tokens':2}}]\n"
                "for event in events: print(json.dumps(event))\n",
                encoding="utf-8")
            fake_cli.chmod(0o755)

            env = os.environ.copy()
            env.update({"AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
                        "HOST_MODEL_IPC_DIR": str(ipc),
                        "CODEX_EXE": str(fake_cli)})
            with patch.dict(os.environ, env, clear=False):
                backend._stage_host_repo(out, runner, schema, instructions,
                                         prompt, workspace)
            broker_script = ROOT / "runtime" / "host_model_ipc_broker_v1.py"
            broker = subprocess.Popen([
                sys.executable, str(broker_script), "--ipc", str(ipc),
                "--repo", str(host_repo), "--once"], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                completed = subprocess.run([
                    sys.executable, str(runner), sys.executable, "unused-node",
                    str(prompt), str(workspace), str(out / "runner"),
                    "handle", "-", str(instructions), str(schema)],
                    env=env, capture_output=True, text=True, timeout=10)
                broker_out, broker_err = broker.communicate(timeout=10)
            finally:
                if broker.poll() is None:
                    broker.kill()
                    broker.wait(timeout=5)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(broker.returncode, 0, broker_err or broker_out)
            process = json.loads((out / "runner" / "process.json").read_text())
            receipt = json.loads((ipc / (process["request_id"] + ".broker.json")).read_text())
            self.assertEqual(receipt["resolved_paths"], {
                "schema": str(schema.resolve()),
                "working": str(workspace.resolve()), "image": None})
            with patch.dict(os.environ, {
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
                "AGENT_INTERFACE_DOCKER_RUNNER": str(runner)}, clear=False):
                backend._verify_host_repo_mapping(
                    out, schema, instructions, workspace, None)
            from runtime.docker_schema_preflight_v1 import validate_model_response
            self.assertEqual(validate_model_response(
                out / "runner" / "events.jsonl", schema)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
