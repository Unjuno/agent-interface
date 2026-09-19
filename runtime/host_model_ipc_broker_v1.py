"""Host-side broker for container_host_model_ipc_runner_v1."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def host_path(value: str | None, repo: Path) -> str | None:
    if value is None:
        return None
    if value == "/repo":
        return str(repo)
    if value.startswith("/repo/"):
        return str(repo / value[6:].replace("/", os.sep))
    return value


def serve(ipc: Path, repo: Path, once: bool = False) -> int:
    cli = os.environ.get("CODEX_EXE", "codex.exe")
    handled = set()
    while True:
        requests = sorted(ipc.glob("*.request.json"))
        for path in requests:
            request = json.loads(path.read_text(encoding="utf-8"))
            request_id = request["request_id"]
            if request_id in handled:
                continue
            args = [cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                    "--sandbox", "read-only", "--skip-git-repo-check", "--json",
                    "--model", "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"',
                    "-c", "project_doc_max_bytes=0", "--output-schema",
                    host_path(request["schema"], repo)]
            if request.get("image"):
                args.extend(["--image", host_path(request["image"], repo)])
            args.extend(["-C", host_path(request["working"], repo), "-"])
            try:
                completed = subprocess.run(args, input=request["prompt"] + "\n",
                                           text=True, encoding="utf-8", errors="replace",
                                           capture_output=True, check=False)
                broker = {
                    "request_id": request_id, "returncode": completed.returncode,
                    "stderr": (completed.stderr or "")[-2000:],
                    "boundary": "host-local-codex-exe",
                    "authority_granted": False,
                }
                response = completed.stdout or ""
            except OSError as exc:
                broker = {
                    "request_id": request_id, "returncode": None,
                    "error_class": type(exc).__name__,
                    "stop_reason": "HOST_BROKER_EXECUTABLE_UNAVAILABLE",
                    "stderr": str(exc)[-2000:],
                    "boundary": "host-local-codex-exe",
                    "authority_granted": False,
                }
                response = ""
            out = ipc / f"{request_id}.response.jsonl"
            out.write_text(response, encoding="utf-8", newline="\n")
            (ipc / f"{request_id}.broker.json").write_text(
                json.dumps(broker) + "\n", encoding="utf-8", newline="\n")
            handled.add(request_id)
            if once:
                return broker.get("returncode") or 1
        time.sleep(.05)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ipc", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--once", action="store_true")
    args = parser.parse_args(); args.ipc.mkdir(parents=True, exist_ok=True)
    return serve(args.ipc.resolve(), args.repo.resolve(), args.once)


if __name__ == "__main__":
    raise SystemExit(main())
