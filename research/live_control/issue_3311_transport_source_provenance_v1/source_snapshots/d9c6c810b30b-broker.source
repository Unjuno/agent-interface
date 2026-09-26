"""Host-side broker for container_host_model_ipc_runner_v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import shutil
import subprocess
import time


def host_path(value: str | None, repo: Path) -> str | None:
    if value is None:
        return None
    if value == "/repo":
        return str(repo)
    if value.startswith("/repo/"):
        relative = PurePosixPath(value).parts[2:]
        if any(part in ("", ".", "..") for part in relative):
            raise ValueError("container path escapes the declared /repo mount")
        candidate = repo.joinpath(*relative)
        if repo.is_absolute():
            root = repo.resolve()
            candidate = candidate.resolve()
            candidate.relative_to(root)
        return str(candidate)
    raise ValueError("container path is outside the declared /repo mount")


def sha(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable_identity(command: str) -> dict:
    resolved = shutil.which(command)
    if resolved is None:
        candidate = Path(command)
        if candidate.is_file():
            resolved = str(candidate)
        else:
            raise FileNotFoundError("configured host executable not found: " + command)
    canonical = str(Path(resolved).resolve())
    version = subprocess.run([resolved, "--version"], capture_output=True,
        text=True, check=True, timeout=15).stdout.strip()
    identity = {"path": canonical, "sha256": sha(canonical), "version": version}
    node = shutil.which("node")
    if node:
        node_path = str(Path(node).resolve())
        node_version = subprocess.run([node, "--version"], capture_output=True,
            text=True, check=True, timeout=15).stdout.strip()
        identity["node"] = {"path": node_path, "sha256": sha(node_path),
                             "version": node_version}
    else:
        identity["node"] = None
    return identity


def build_command(request: dict, repo: Path, cli: str) -> list[str]:
    if request.get("authority_granted") is not False:
        raise ValueError("host IPC broker refuses authority-bearing requests")
    if request.get("mode") not in ("coordinate", "handle"):
        raise ValueError("unsupported host IPC mode")
    image_value = request.get("image")
    if (request["mode"] == "coordinate") != bool(image_value):
        raise ValueError("host IPC mode/image mismatch")
    schema = host_path(request["schema"], repo)
    instructions = host_path(request["instructions"], repo)
    working = host_path(request["working"], repo)
    image = host_path(image_value, repo) if image_value else None
    for path, field in ((schema, "schema_sha256"),
                        (instructions, "instructions_sha256"),
                        (image, "image_sha256")):
        if path is not None:
            if not Path(path).is_file():
                raise FileNotFoundError(path)
            if request.get(field) != sha(path):
                raise ValueError("host IPC asset digest mismatch: " + field)
    if not Path(working).is_dir():
        raise FileNotFoundError(working)
    args = [cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
            "--sandbox", "read-only", "--skip-git-repo-check", "--json",
            "--model", "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"',
            "-c", "project_doc_max_bytes=0", "-c",
            "model_instructions_file=" + json.dumps(instructions),
            "--output-schema", schema]
    if image is not None:
        args.extend(["--image", image])
    args.extend(["-C", working, "-"])
    return args


def serve(ipc: Path, repo: Path, once: bool = False) -> int:
    cli = os.environ.get("CODEX_EXE", "codex.exe")
    timeout_s = float(os.environ.get("HOST_MODEL_BROKER_TIMEOUT_S", "90"))
    handled = set()
    while True:
        requests = sorted(ipc.glob("*.request.json"))
        for path in requests:
            request = json.loads(path.read_text(encoding="utf-8"))
            request_id = request["request_id"]
            if request_id in handled:
                continue
            started_ns = time.perf_counter_ns()
            host_cli_invoked = False
            cli_spawn_attempted = False
            identity = None
            try:
                args = build_command(request, repo, cli)
                identity = executable_identity(cli)
                cli_spawn_attempted = True
                host_cli_invoked = True
                completed = subprocess.run(args, input=request["prompt"] + "\n",
                                           text=True, encoding="utf-8", errors="replace",
                                           capture_output=True, check=False, timeout=timeout_s)
                broker = {"request_id": request_id, "returncode": completed.returncode,
                          "stderr": (completed.stderr or "")[-2000:],
                          "boundary": "host-local-codex-exe", "authority_granted": False,
                          "host_cli_invoked": host_cli_invoked,
                          "host_cli_spawn_attempted": cli_spawn_attempted,
                          "host_cli_identity": identity,
                          "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                response = completed.stdout or ""
            except subprocess.TimeoutExpired as exc:
                broker = {"request_id": request_id, "returncode": None,
                          "error_class": "TimeoutExpired",
                          "stop_reason": ("HOST_BROKER_SUBPROCESS_TIMEOUT" if cli_spawn_attempted
                                          else "HOST_CLI_IDENTITY_TIMEOUT"),
                          "timeout_s": timeout_s, "stderr": str(exc)[-2000:],
                          "boundary": "host-local-codex-exe", "authority_granted": False,
                          "host_cli_invoked": host_cli_invoked,
                          "host_cli_spawn_attempted": cli_spawn_attempted,
                          "host_cli_identity": identity,
                          "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                response = ""
            except OSError as exc:
                broker = {"request_id": request_id, "returncode": None,
                          "error_class": type(exc).__name__,
                          "stop_reason": ("HOST_BROKER_EXECUTABLE_UNAVAILABLE" if cli_spawn_attempted
                                          else "HOST_BROKER_REQUEST_REFUSED"),
                          "stderr": str(exc)[-2000:],
                          "boundary": "host-local-codex-exe", "authority_granted": False,
                          "host_cli_invoked": host_cli_invoked,
                          "host_cli_spawn_attempted": cli_spawn_attempted,
                          "host_cli_identity": identity,
                          "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                response = ""
            except Exception as exc:
                broker = {"request_id": request_id, "returncode": None,
                          "error_class": type(exc).__name__,
                          "stop_reason": "HOST_BROKER_REQUEST_REFUSED",
                          "stderr": str(exc)[-2000:],
                          "boundary": "host-local-codex-exe", "authority_granted": False,
                          "host_cli_invoked": False,
                          "host_cli_spawn_attempted": cli_spawn_attempted,
                          "host_cli_identity": identity,
                          "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                response = ""
            (ipc / f"{request_id}.response.jsonl").write_text(
                response, encoding="utf-8", newline="\n")
            (ipc / f"{request_id}.broker.json").write_text(
                json.dumps(broker) + "\n", encoding="utf-8", newline="\n")
            handled.add(request_id)
            if once:
                return_code = broker.get("returncode")
                return return_code if return_code is not None else 1
        time.sleep(.05)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ipc", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--once", action="store_true")
    args = parser.parse_args(); args.ipc.mkdir(parents=True, exist_ok=True)
    return serve(args.ipc.resolve(), args.repo.resolve(), args.once)


if __name__ == "__main__":
    raise SystemExit(main())
