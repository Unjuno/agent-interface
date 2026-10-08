from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "research/live_control/docker_model_call_backend_v1.py"
BROKER = ROOT / "runtime/host_model_ipc_broker_v1.py"
RUN = Path(__file__).resolve().parent / "evidence/seed-284920"
INNER = "sha256:" + "0" * 64


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if RUN.exists():
        raise RuntimeError("STOP_EVIDENCE_PATH_EXISTS")
    RUN.mkdir(parents=True)
    backend = load("v20_backend", BASE)
    broker = load("v20_broker", BROKER)
    with tempfile.TemporaryDirectory(prefix="issue2849-v20-") as temp:
        root = Path(temp) / "call-output"
        root.mkdir()
        image = Path(temp) / "capture.png"
        prompt = Path(temp) / "prompt.txt"
        schema = Path(temp) / "schema.json"
        instructions = Path(temp) / "instructions.txt"
        runner = Path(temp) / "runner.py"
        workspace = Path(temp) / "workspace"
        ipc = Path(temp) / "ipc"
        for path in (image, prompt, schema, instructions, runner):
            path.write_text("contract-only\n")
        workspace.mkdir()
        ipc.mkdir()
        os.environ.update({
            "AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
            "AGENT_INTERFACE_DOCKER_SCHEMA": str(schema),
            "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(instructions),
            "AGENT_INTERFACE_DOCKER_IMAGE": INNER,
            "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
            "DOCKER": "docker",
        })
        command = backend.build_command(root, prompt, image, "plain", workspace)
        # The production backend treats DOCKER as one executable, not a shell command.
        # Check the exact command construction and explicitly flag context support status.
        args = command
        mounts = [args[i + 1] for i, item in enumerate(args[:-1]) if item == "-v"]
        host_root = next(value.split(":", 1)[0] for value in mounts if value.endswith(":/out"))
        host_workspace = next(value.split(":", 1)[0] for value in mounts if value.endswith(":/repo/workspace"))
        translated = broker.host_path("/repo/workspace", Path(host_root))
        docker_info = subprocess.run(
            ["docker", "--context", "orbstack", "info", "--format", "{{.ServerVersion}} {{.OperatingSystem}}/{{.Architecture}}"],
            capture_output=True, text=True, timeout=20, check=False)
        checks = {
            "backend_command_constructed_without_execution": bool(command) and command[0] == "docker",
            "orb_stack_daemon_reachable_read_only": docker_info.returncode == 0 and bool(docker_info.stdout.strip()),
            "backend_has_no_context_selector": "--context" not in command,
            "backend_workspace_maps_to_broker_workspace": Path(translated) == Path(host_workspace),
            "broker_repo_path_translation_contained": Path(translated).resolve().is_relative_to(Path(host_root).resolve()),
            "backend_call_root_precondition_is_new_directory": root.exists(),
            "no_task_or_model_or_container_invoked": True,
        }
        result = {
            "issue": 2849, "seed": 284920, "status": "PASS_CONTRACT" if all(checks.values()) else "STOP_CONTRACT",
            "checks": checks, "command": command, "mounts": mounts,
            "host_root": host_root, "host_workspace": host_workspace,
            "broker_workspace_translation": translated,
            "docker_info": {"returncode": docker_info.returncode,
                            "stdout": docker_info.stdout[-2000:], "stderr": docker_info.stderr[-2000:]},
            "authority_granted": False, "task_started": False, "model_calls": 0,
            "containers_started": 0,
        }
        (RUN / "contract-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        evidence = sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
        (RUN / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in evidence))
        return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
