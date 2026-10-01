"""One no-model OrbStack round trip through the existing v1 IPC boundary.

The fake CLI validates host-visible schema and workspace paths, then emits a
synthetic event stream. This proves transport mechanics only, not model,
preflight, GUI, task, or efficiency behavior.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "runtime"
LIVE = ROOT / "research/live_control"
IMAGE = "agent-interface-3311-runtime-v2:20260920"


class OrbStackV1TransportTest(unittest.TestCase):
    def test_fake_cli_round_trip_over_shared_mounts(self):
        evidence_path = os.environ.get("AGENT_INTERFACE_3311_V1_EVIDENCE_DIR")
        context = nullcontext(evidence_path) if evidence_path else tempfile.TemporaryDirectory(
            prefix="3311-v1-ipc-")
        with context as temp:
            root = Path(temp)
            if evidence_path:
                root.mkdir(parents=True, exist_ok=False)
            repo, ipc, out = root / "repo", root / "ipc", root / "out"
            workspace = repo / "workspace"
            workspace.mkdir(parents=True); ipc.mkdir(); out.mkdir()
            (repo / "prompt.txt").write_text("no-model transport probe\n", encoding="utf-8")
            (repo / "instructions.txt").write_text("synthetic only\n", encoding="utf-8")
            (repo / "schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
            fake = root / "fake-codex"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "a=sys.argv\n"
                "if a[1:] == ['--version']:\n"
                " print('codex fake-transport-v1'); raise SystemExit(0)\n"
                "schema=a[a.index('--output-schema')+1]\n"
                "work=a[a.index('-C')+1]\n"
                "instructions=next(v.split('=',1)[1] for v in a if v.startswith('model_instructions_file='))\n"
                "if not os.path.isfile(schema) or not os.path.isdir(work): raise SystemExit(81)\n"
                "if not os.path.isfile(json.loads(instructions)): raise SystemExit(82)\n"
                "print(json.dumps({'type':'thread.started','thread_id':'synthetic-v1'}))\n"
                "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'{}'}}))\n"
                "print(json.dumps({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}))\n",
                encoding="utf-8")
            fake.chmod(0o755)
            env = dict(os.environ, CODEX_EXE=str(fake))
            broker = subprocess.Popen([sys.executable, str(RUNTIME / "host_model_ipc_broker_v1.py"),
                "--ipc", str(ipc), "--repo", str(repo), "--once"], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            command = ["docker", "--context", "orbstack", "run", "--rm", "--network", "none",
                "-e", "HOST_MODEL_IPC_DIR=/ipc", "-e", "HOST_MODEL_IPC_TIMEOUT_S=15",
                "-v", f"{ipc}:/ipc", "-v", f"{repo}:/repo", "-v", f"{out}:/out",
                "-v", f"{LIVE / 'container_host_model_ipc_runner_v1.py'}:/code/runner.py:ro",
                "--entrypoint", "/usr/bin/python3", IMAGE,
                "/code/runner.py", "/usr/bin/node", "/usr/bin/true", "/repo/prompt.txt",
                "/repo/workspace", "/out/runner", "handle", "-",
                "/repo/instructions.txt", "/repo/schema.json"]
            image_info = subprocess.run(["docker", "--context", "orbstack", "image",
                "inspect", IMAGE], capture_output=True, text=True, check=True)
            (root / "docker-image-inspect.json").write_text(image_info.stdout, encoding="utf-8")
            (root / "container-command.json").write_text(json.dumps(command, indent=2) + "\n",
                encoding="utf-8")
            container = subprocess.run(command, capture_output=True, text=True,
                                       check=False, timeout=30)
            if broker.poll() is None:
                broker.terminate()
            broker_stdout, broker_stderr = broker.communicate(timeout=5)
            (root / "container.stdout.txt").write_text(container.stdout, encoding="utf-8")
            (root / "container.stderr.txt").write_text(container.stderr, encoding="utf-8")
            (root / "broker.stdout.txt").write_text(broker_stdout, encoding="utf-8")
            (root / "broker.stderr.txt").write_text(broker_stderr, encoding="utf-8")
            if evidence_path:
                (root / "exit-codes.json").write_text(json.dumps({
                    "container": container.returncode, "broker": broker.returncode,
                }, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(container.returncode, 0,
                container.stderr + "\nBROKER=" + broker_stdout + broker_stderr)
            self.assertEqual(broker.returncode, 0, broker_stderr or broker_stdout)
            request_files = list(ipc.glob("*.request.json"))
            self.assertEqual(len(request_files), 1)
            request = json.loads(request_files[0].read_text(encoding="utf-8"))
            self.assertFalse(request["authority_granted"])
            self.assertEqual(request["schema"], "/repo/schema.json")
            self.assertEqual(request["working"], "/repo/workspace")
            broker_record = json.loads((ipc / f"{request['request_id']}.broker.json").read_text())
            self.assertEqual(broker_record["returncode"], 0)
            self.assertTrue(broker_record["host_cli_invoked"])
            self.assertEqual(broker_record["host_cli_identity"]["version"],
                             "codex fake-transport-v1")
            self.assertEqual(broker_record["host_cli_identity"]["path"], str(fake.resolve()))
            self.assertEqual(len(broker_record["host_cli_identity"]["sha256"]), 64)
            self.assertIsNotNone(broker_record["host_cli_identity"]["node"])
            events = [json.loads(line) for line in
                      (out / "runner/events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["type"] for row in events],
                             ["thread.started", "item.completed", "turn.completed"])
            process = json.loads((out / "runner/process.json").read_text(encoding="utf-8"))
            self.assertFalse(process["authority_granted"])
            self.assertEqual(process["boundary"], "container-to-host-model-ipc")
            if evidence_path:
                (root / "source-sha256.json").write_text(json.dumps({
                    "broker_sha256": hashlib.sha256((RUNTIME / "host_model_ipc_broker_v1.py").read_bytes()).hexdigest(),
                    "runner_sha256": hashlib.sha256((LIVE / "container_host_model_ipc_runner_v1.py").read_bytes()).hexdigest(),
                    "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
