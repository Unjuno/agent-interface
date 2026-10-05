"""Run one inert host-IPC path integration boundary experiment."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
LIVE = ROOT / "research" / "live_control"
sys.path.insert(0, str(LIVE))
import docker_model_call_backend_v1 as backend


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path) -> int:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    host_repo = output / "broker-repo"
    host_repo.mkdir()
    ipc = output / "ipc"
    ipc.mkdir()
    workspace = output / "workspace"
    workspace.mkdir()
    out = output / "out"
    out.mkdir()
    schema = output / "schema.json"
    schema.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object", "properties": {"compatible": {"const": True}},
        "required": ["compatible"], "additionalProperties": False,
    }, sort_keys=True) + "\n", encoding="utf-8")
    instructions = output / "instructions.txt"
    instructions.write_text("fixed inert IPC boundary instruction\n", encoding="utf-8")
    prompt = out / "prompt.txt"
    prompt.write_text("return compatible true\n", encoding="utf-8")
    fake_cli = output / "fake-codex"
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
                "HOST_MODEL_IPC_DIR": str(ipc), "CODEX_EXE": str(fake_cli)})
    os.environ.update({"AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
                       "HOST_MODEL_IPC_DIR": str(ipc)})
    runner = LIVE / "container_host_model_ipc_runner_v1.py"
    broker_script = ROOT / "runtime" / "host_model_ipc_broker_v1.py"
    with backend._host_repo_mapping_lock():
        backend._stage_host_repo(out, runner, schema, instructions, prompt, workspace)

    broker_command = [sys.executable, str(broker_script), "--ipc", str(ipc),
                      "--repo", str(host_repo), "--once"]
    runner_command = [sys.executable, str(runner), sys.executable, "unused-node",
                      str(prompt), str(workspace), str(out / "runner"), "handle", "-",
                      str(instructions), str(schema)]
    write_json(output / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "system": platform.system(), "machine": platform.machine(),
        "container_launched": False, "real_model_called": False,
        "gui_or_native_input": False, "network_enabled_by_harness": False,
    })
    write_json(output / "commands.json", {
        "broker": broker_command, "runner": runner_command,
        "fake_cli": str(fake_cli), "timeout_seconds": 10,
    })
    started_ns = time.time_ns()
    broker = subprocess.Popen(broker_command, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True)
    try:
        completed = subprocess.run(runner_command, env=env, capture_output=True,
                                   text=True, timeout=10, check=False)
        broker_stdout, broker_stderr = broker.communicate(timeout=10)
    finally:
        if broker.poll() is None:
            broker.kill()
            broker.wait(timeout=5)
    (output / "runner.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output / "runner.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (output / "broker.stdout.txt").write_text(broker_stdout, encoding="utf-8")
    (output / "broker.stderr.txt").write_text(broker_stderr, encoding="utf-8")
    request_files = sorted(ipc.glob("*.request.json"))
    request_id = request_files[0].name.removesuffix(".request.json") if request_files else None
    write_json(output / "execution.json", {
        "started_ns": started_ns, "ended_ns": time.time_ns(),
        "runner_returncode": completed.returncode,
        "broker_returncode": broker.returncode,
        "request_id": request_id,
    })
    if request_id:
        process = json.loads((out / "runner" / "process.json").read_text(encoding="utf-8"))
        events = (out / "runner" / "events.jsonl").read_bytes()
        if process.get("request_id") != request_id:
            raise RuntimeError("runner process receipt request id mismatch")
        (output / "runner.process.json").write_bytes(
            (out / "runner" / "process.json").read_bytes())
        (output / "runner.events.jsonl").write_bytes(events)
        for suffix in ("request.json", "broker.json", "response.jsonl"):
            source = ipc / (request_id + "." + suffix)
            if source.is_file():
                (output / ("ipc." + suffix)).write_bytes(source.read_bytes())
    write_json(output / "source_sha256.json", {
        str(path.relative_to(ROOT)): sha256(path) for path in (
            Path(__file__).resolve(), LIVE / "docker_model_call_backend_v1.py",
            runner, broker_script,
            ROOT / "runtime" / "docker_schema_preflight_v1.py",
        )
    })
    print(json.dumps({"runner_returncode": completed.returncode,
                      "broker_returncode": broker.returncode,
                      "request_id": request_id,
                      "output": str(output)}, indent=2))
    return 0 if completed.returncode == 0 and broker.returncode == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_experiment.py FRESH_OUTPUT_DIRECTORY")
    raise SystemExit(run(Path(sys.argv[1])))
