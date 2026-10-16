"""Host-side broker for container_host_model_ipc_runner_v1."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def host_path(value: str | None, repo: Path) -> str | None:
    if value is None:
        return None
    if value == "/repo":
        return str(repo)
    if value.startswith("/repo/"):
        return str(repo / value[6:].replace("/", os.sep))
    if value == "/workspace":
        return str(repo)
    if value.startswith("/workspace/"):
        return str(repo / value[11:].replace("/", os.sep))
    return value


MAX_INSTRUCTION_BYTES = 1024 * 1024


def verified_instruction_bytes(request: dict) -> bytes | None:
    value = request.get("instructions_b64")
    if value is None:
        if request.get("instructions") is not None:
            raise ValueError("path-based instructions are not accepted")
        return None
    if not isinstance(value, str):
        raise ValueError("instructions_b64 must be a string")
    if len(value) > ((MAX_INSTRUCTION_BYTES + 2) // 3) * 4:
        raise ValueError("instruction payload exceeds size limit")
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("instruction payload is not valid base64") from exc
    if len(data) > MAX_INSTRUCTION_BYTES:
        raise ValueError("instruction payload exceeds size limit")
    expected = request.get("instructions_sha256")
    actual = hashlib.sha256(data).hexdigest()
    if not isinstance(expected, str) or not hmac.compare_digest(expected, actual):
        raise ValueError("instruction SHA-256 mismatch")
    return data

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
            try:
                instruction_bytes = verified_instruction_bytes(request)
            except (OSError, ValueError) as exc:
                broker = {"request_id": request_id, "returncode": None,
                          "error_class": "InvalidInstructions",
                          "stop_reason": "HOST_MODEL_INSTRUCTIONS_REJECTED",
                          "stderr": str(exc)[-2000:],
                          "boundary": "host-local-codex-exe", "authority_granted": False,
                          "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                response = ""
            else:
                try:
                    with tempfile.TemporaryDirectory(prefix="host-model-instructions-") as temp_dir:
                        args = [cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                                "--sandbox", "read-only", "--skip-git-repo-check", "--json",
                                "--model", "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"',
                                "-c", "project_doc_max_bytes=0"]
                        if instruction_bytes is not None:
                            private_instructions = Path(temp_dir) / "instructions.txt"
                            private_instructions.write_bytes(instruction_bytes)
                            args.extend(["-c", "model_instructions_file=" + json.dumps(
                                private_instructions.as_posix())])
                        args.extend(["--output-schema", host_path(request["schema"], repo)])
                        if request.get("image"):
                            args.extend(["--image", host_path(request["image"], repo)])
                        args.extend(["-C", host_path(request["working"], repo), "-"])
                        completed = subprocess.run(args, input=request["prompt"] + "\n",
                                                   text=True, encoding="utf-8", errors="replace",
                                                   capture_output=True, check=False, timeout=timeout_s)
                    broker = {"request_id": request_id, "returncode": completed.returncode,
                              "stderr": (completed.stderr or "")[-2000:],
                              "boundary": "host-local-codex-exe", "authority_granted": False,
                              "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                    response = completed.stdout or ""
                except subprocess.TimeoutExpired as exc:
                    broker = {"request_id": request_id, "returncode": None,
                              "error_class": "TimeoutExpired", "stop_reason": "HOST_BROKER_SUBPROCESS_TIMEOUT",
                              "timeout_s": timeout_s, "stderr": str(exc)[-2000:],
                              "boundary": "host-local-codex-exe", "authority_granted": False,
                              "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                    response = ""
                except OSError as exc:
                    broker = {"request_id": request_id, "returncode": None,
                              "error_class": type(exc).__name__,
                              "stop_reason": "HOST_BROKER_EXECUTABLE_UNAVAILABLE",
                              "stderr": str(exc)[-2000:],
                              "boundary": "host-local-codex-exe", "authority_granted": False,
                              "started_ns": started_ns, "exited_ns": time.perf_counter_ns()}
                    response = ""
            (ipc / f"{request_id}.response.jsonl").write_text(
                response, encoding="utf-8", newline="\n")
            def resolved_path(key):
                value = host_path(request.get(key), repo)
                return None if value is None else str(Path(value).resolve())
            broker["resolved_paths"] = {
                "schema": resolved_path("schema"),
                "working": resolved_path("working"),
                "image": resolved_path("image"),
            }
            (ipc / f"{request_id}.broker.json").write_text(
                json.dumps(broker) + "\n", encoding="utf-8", newline="\n")
            handled.add(request_id)
            if once:
                return broker["returncode"] if broker["returncode"] is not None else 1
        time.sleep(.05)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ipc", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--once", action="store_true")
    args = parser.parse_args(); args.ipc.mkdir(parents=True, exist_ok=True)
    return serve(args.ipc.resolve(), args.repo.resolve(), args.once)


if __name__ == "__main__":
    raise SystemExit(main())
