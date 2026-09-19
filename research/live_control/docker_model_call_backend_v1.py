"""Docker-backed model-call contract for the integrated-efficiency seam.

This module deliberately requires explicit paths and image configuration. It
does not fall back to the legacy WSL caller and reports malformed/missing
container receipts as failures.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess


def build_command(root: Path, prompt: str, image: Path, contract: str, workspace: Path) -> list[str]:
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    schema = os.environ.get("AGENT_INTERFACE_DOCKER_SCHEMA", "")
    instructions = os.environ.get("AGENT_INTERFACE_DOCKER_INSTRUCTIONS", "")
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    if not all((runner, schema, instructions, image_name, ipc)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    if contract not in ("plain", "compiled"):
        raise ValueError("contract must be plain or compiled")
    for value in (prompt, image, workspace, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    root.mkdir(parents=True, exist_ok=False)
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
    prompt_path = root / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\\n")
    command = build_command(root, prompt_path, image, contract, workspace)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("STOP_DOCKER_BACKEND_RUNNER:" + str(completed.returncode))
    receipt = root / "runner" / "process.json"
    events = root / "runner" / "events.jsonl"
    if not receipt.is_file() or not events.is_file():
        raise RuntimeError("STOP_DOCKER_BACKEND_MISSING_RECEIPT")
    from integrated_efficiency_model_v1 import parse
    return parse(root / "runner", contract)
