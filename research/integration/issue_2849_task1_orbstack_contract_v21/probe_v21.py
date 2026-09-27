from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence/seed-284921"
OUTER = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
SOCKET = Path("/Users/taka/.orbstack/run/docker.sock")
BACKEND = ROOT / "research/live_control/docker_model_call_backend_v1.py"
BROKER = ROOT / "runtime/host_model_ipc_broker_v1.py"


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
    if not SOCKET.exists():
        raise RuntimeError("STOP_ORBSTACK_SOCKET_MISSING")
    RUN.mkdir(parents=True)
    backend = load("v21_backend", BACKEND)
    broker = load("v21_broker", BROKER)
    image_id = subprocess.check_output(
        ["docker", "--context", "orbstack", "image", "inspect", OUTER,
         "--format", "{{.Id}} {{.Architecture}}"], text=True, timeout=20).strip()
    if image_id != OUTER + " arm64":
        raise RuntimeError("STOP_OUTER_IMAGE_IDENTITY:" + image_id)

    with tempfile.TemporaryDirectory(prefix="issue2849-v21-") as temp:
        base = Path(temp)
        mirror = base / "mirror"
        workspace = mirror / "workspace"
        workspace.mkdir(parents=True)
        ipc = base / "ipc"
        ipc.mkdir()
        call_root = base / "model-calls" / "plain" / "call-001"
        call_root.parent.mkdir(parents=True)
        prompt, capture = base / "prompt.txt", base / "capture.png"
        runner, schema, instructions = (mirror / name for name in
                                       ("runner.py", "schema.json", "instructions.txt"))
        for path in (prompt, capture, runner, schema, instructions):
            path.write_text("contract fixture\n")
        os.environ.update({
            "AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
            "AGENT_INTERFACE_DOCKER_SCHEMA": str(schema),
            "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(instructions),
            "AGENT_INTERFACE_DOCKER_IMAGE": OUTER,
            "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
            "DOCKER": "docker",
        })
        argv = backend.build_command(call_root, prompt, capture, "plain", workspace)
        mounts = [argv[i + 1] for i, token in enumerate(argv[:-1]) if token == "-v"]
        out_mount = next(value for value in mounts if value.endswith(":/out"))
        workspace_mount = next(value for value in mounts if value.endswith(":/repo/workspace"))
        host_out = Path(out_mount.rsplit(":", 1)[0]).resolve()
        host_workspace = Path(workspace_mount.rsplit(":", 1)[0]).resolve()
        broker_workspace = Path(broker.host_path("/repo/workspace", mirror)).resolve()

        # One bounded, network-disabled container invocation; only the read-only
        # Docker version endpoint is exercised through the mounted OrbStack socket.
        command = ["docker", "--context", "orbstack", "run", "--rm", "--network", "none",
                   "--mount", f"type=bind,src={SOCKET},dst=/var/run/docker.sock",
                   "-e", "DOCKER_HOST=unix:///var/run/docker.sock",
                   "--entrypoint", "docker", OUTER, "version", "--format",
                   "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"]
        (RUN / "frozen-inputs.json").write_text(json.dumps({
            "seed": 284921, "preregistration_comment": 5751989914,
            "main_commit": subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(),
            "outer_image": image_id, "socket": str(SOCKET), "socket_sha256": sha(SOCKET) if SOCKET.is_file() else None,
            "backend_sha256": sha(BACKEND), "broker_sha256": sha(BROKER),
            "probe_sha256": sha(Path(__file__)), "authority_granted": False,
            "task_started": False, "model_calls": 0, "max_container_invocations": 1,
        }, indent=2, sort_keys=True) + "\n")
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
        checks = {
            "pinned_outer_image_identity": image_id == OUTER + " arm64",
            "outer_container_socket_daemon_query": result.returncode == 0 and bool(result.stdout.strip()),
            "backend_workspace_mount_is_broker_mirror_workspace": host_workspace == broker_workspace,
            "backend_output_root_is_unique_child_of_call_root": host_out == call_root.resolve(),
            "backend_argv_network_disabled": "none" in argv and "--network" in argv,
            "host_broker_repo_translation_contained": broker_workspace.is_relative_to(mirror.resolve()),
            "formal_task_or_model_call_invoked": False,
        }
        receipt = {
            "seed": 284921, "status": "PASS_CONSTRUCTION" if all(checks.values()) else "STOP_CONSTRUCTION",
            "checks": checks, "backend_argv": argv, "backend_mounts": mounts,
            "call_root": str(call_root), "backend_host_output_root": str(host_out),
            "backend_host_workspace": str(host_workspace), "broker_workspace": str(broker_workspace),
            "socket_probe_command": command,
            "socket_probe": {"returncode": result.returncode, "stdout": result.stdout[-2000:],
                             "stderr": result.stderr[-2000:]},
            "task_started": False, "host_broker_started": False, "model_calls": 0,
            "container_invocations": 1, "authority_granted": False,
        }
        (RUN / "contract-result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    files = sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (RUN / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if receipt["status"] == "PASS_CONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
