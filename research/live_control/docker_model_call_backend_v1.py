"""Docker-backed model-call contract for the integrated-efficiency seam.

This module deliberately requires explicit paths and image configuration. It
does not fall back to the legacy WSL caller and reports malformed/missing
container receipts as failures.
"""
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
import subprocess
import time

CLIENT_TIMEOUT_SECONDS = 90


def _diagnostic_tail(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    return (value or '')[-2000:]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight_identity(schema: Path, instructions: Path):
    """Identity for the handle/no-image schema probe over host-model IPC."""
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    if not all((runner, image_name, ipc)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    for value in (runner, instructions, schema, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    identity = {
        "schema_sha256": _sha(schema),
        "requested_model": "gpt-5.6-luna",
        "requested_effort": "low",
        "runner_sha256": _sha(runner),
        "instructions_sha256": _sha(instructions),
        "container_image": image_name,
        "model_boundary": "container-to-host-model-ipc",
        "request_shape": "container_host_model_ipc_runner_v1:handle:no-image:output-schema",
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return identity, hashlib.sha256(encoded).hexdigest()


def build_preflight_command(output: Path, prompt: Path, workspace: Path,
                            instructions: Path, schema: Path) -> list[str]:
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    if not all((runner, image_name, ipc)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    for value in (runner, prompt, workspace, instructions, schema, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    output = Path(output).resolve()
    parent = output.parent
    if not parent.is_dir() or output.exists():
        raise FileNotFoundError(output) if not parent.is_dir() else FileExistsError(output)
    return [
        os.environ.get("DOCKER", "docker"), "run", "--rm", "--network", "none",
        "-e", "HOST_MODEL_IPC_DIR=/ipc",
        "-v", f"{parent}:/out",
        "-v", f"{Path(ipc).resolve()}:/ipc",
        "-v", f"{Path(runner).resolve()}:/repo/runner.py:ro",
        "-v", f"{Path(instructions).resolve()}:/repo/instructions.txt:ro",
        "-v", f"{Path(prompt).resolve()}:/repo/prompt.txt:ro",
        "-v", f"{Path(schema).resolve()}:/repo/schema.json:ro",
        "-v", f"{Path(workspace).resolve()}:/repo/workspace",
        image_name, "python", "/repo/runner.py",
        "/usr/bin/node", "/usr/bin/true", "/repo/prompt.txt",
        "/repo/workspace", "/out/" + output.name, "handle", "-",
        "/repo/instructions.txt", "/repo/schema.json",
    ]


def preflight_call(prompt: Path, workspace: Path, output: Path,
                   instructions: Path, schema: Path):
    """Execute the no-image `handle` request via Docker-host IPC exactly once."""
    output = Path(output).resolve()
    command = build_preflight_command(output, prompt, workspace, instructions, schema)
    attempt_path = output.parent / "preflight-client-attempt.json"
    result_path = output.parent / "preflight-client-result.json"
    attempt_path.write_text(json.dumps({
        "status": "starting", "started_ns": time.time_ns(),
        "timeout_seconds": CLIENT_TIMEOUT_SECONDS, "command": command,
        "mode": "handle", "image": None,
    }, indent=2) + "\n", encoding="utf-8")
    try:
        completed = subprocess.run(command, capture_output=True, check=False,
                                   timeout=CLIENT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        for name, value in (("stdout", error.stdout), ("stderr", error.stderr)):
            (output.parent / ("preflight-runner-" + name + ".txt")).write_text(
                _diagnostic_tail(value), encoding="utf-8")
        result_path.write_text(json.dumps({
            "status": "STOP_DOCKER_PREFLIGHT_TIMEOUT", "ended_ns": time.time_ns(),
            "returncode": None, "container_state": "unknown",
            "host_model_state": "unknown", "retry_performed": False,
        }, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_TIMEOUT; remote execution state unknown; no retry") from error
    result_path.write_text(json.dumps({
        "status": "returned", "ended_ns": time.time_ns(),
        "returncode": completed.returncode,
    }, indent=2) + "\n", encoding="utf-8")
    return completed


def _contract_path(variable: str, contract: str) -> str:
    return (os.environ.get(variable + "_" + contract.upper(), "")
            or os.environ.get(variable, ""))


def build_command(root: Path, prompt: str, image: Path, contract: str, workspace: Path) -> list[str]:
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    schema = _contract_path("AGENT_INTERFACE_DOCKER_SCHEMA", contract)
    instructions = _contract_path("AGENT_INTERFACE_DOCKER_INSTRUCTIONS", contract)
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    if not all((runner, schema, instructions, image_name, ipc)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    if contract not in ("plain", "compiled"):
        raise ValueError("contract must be plain or compiled")
    for value in (runner, schema, instructions, prompt, image, workspace, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    return [
        os.environ.get("DOCKER", "docker"), "run", "--rm", "--network", "none",
        "-e", "HOST_MODEL_IPC_DIR=/ipc",
        "-v", f"{Path(root).resolve()}:/out",
        "-v", f"{Path(ipc).resolve()}:/ipc",
        "-v", f"{Path(runner).resolve()}:/repo/runner.py:ro",
        "-v", f"{Path(schema).resolve()}:/repo/schema.json:ro",
        "-v", f"{Path(instructions).resolve()}:/repo/instructions.txt:ro",
        "-v", f"{Path(prompt).resolve()}:/repo/prompt.txt:ro",
        "-v", f"{Path(image).resolve()}:/repo/image.png:ro",
        "-v", f"{Path(workspace).resolve()}:/repo/workspace",
        image_name, "python", "/repo/runner.py",
        "/usr/bin/node", "/usr/bin/true", "/repo/prompt.txt",
        "/repo/workspace", "/out/runner", "coordinate", "/repo/image.png",
        "/repo/instructions.txt", "/repo/schema.json",
    ]


def call(root: Path, prompt: str, image: Path, contract: str, workspace: Path):
    root.mkdir(parents=True, exist_ok=False)
    prompt_path = root / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    command = build_command(root, prompt_path, image, contract, workspace)
    schema_path = Path(_contract_path("AGENT_INTERFACE_DOCKER_SCHEMA", contract))
    (root / 'client-attempt.json').write_text(json.dumps({
        'status': 'starting', 'started_ns': time.time_ns(),
        'timeout_seconds': CLIENT_TIMEOUT_SECONDS, 'command': command,
    }, indent=2) + '\n', encoding='utf-8')
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False,
                                   timeout=CLIENT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        for name, value in (('stdout', error.stdout), ('stderr', error.stderr)):
            (root / ('runner-' + name + '.txt')).write_text(
                _diagnostic_tail(value), encoding='utf-8')
        (root / 'client-result.json').write_text(json.dumps({
            'status': 'STOP_DOCKER_BACKEND_TIMEOUT', 'ended_ns': time.time_ns(),
            'timeout_seconds': CLIENT_TIMEOUT_SECONDS, 'returncode': None,
            'container_state': 'unknown', 'host_model_state': 'unknown',
            'retry_performed': False, 'diagnostic_limit_characters': 2000,
        }, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError('STOP_DOCKER_BACKEND_TIMEOUT; remote execution state unknown; no retry') from error
    (root / 'client-result.json').write_text(json.dumps({
        'status': 'returned', 'ended_ns': time.time_ns(), 'returncode': completed.returncode,
    }, indent=2) + '\n', encoding='utf-8')
    (root / 'runner-stdout.txt').write_text(completed.stdout, encoding='utf-8')
    (root / 'runner-stderr.txt').write_text(completed.stderr, encoding='utf-8')
    if completed.returncode != 0:
        raise RuntimeError("STOP_DOCKER_BACKEND_RUNNER:" + str(completed.returncode))
    receipt = root / "runner" / "process.json"
    events = root / "runner" / "events.jsonl"
    if not receipt.is_file() or not events.is_file():
        raise RuntimeError("STOP_DOCKER_BACKEND_MISSING_RECEIPT")
    from runtime.docker_schema_preflight_v1 import validate_model_response
    validation = validate_model_response(events, schema_path)
    (root / 'schema-validation.json').write_text(
        json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    if validation['status'] != 'PASS':
        raise RuntimeError('STOP_DOCKER_BACKEND_OUTPUT:' + validation['status'])
    from integrated_efficiency_model_v1 import parse
    result = parse(root / "runner", contract)
    (root / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result
