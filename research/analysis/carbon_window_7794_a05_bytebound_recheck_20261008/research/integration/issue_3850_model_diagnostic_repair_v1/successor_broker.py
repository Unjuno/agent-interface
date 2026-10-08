from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def map_path(value: str, repo: Path) -> str:
    if value == "/repo":
        return str(repo)
    if value.startswith("/repo/"):
        return str(repo / value[6:].replace("/", os.sep))
    return value


def serve(ipc: Path, repo: Path) -> int:
    cli = os.environ["CODEX_EXE"]
    timeout = int(os.environ.get("BROKER_TIMEOUT_S", "120"))
    while True:
        paths = sorted(ipc.glob("*.request.json"))
        if paths:
            path = paths[0]
            req = json.loads(path.read_text(encoding="utf-8"))
            rid = req["request_id"]
            started = time.perf_counter_ns()
            argv_capture = {"request_id": rid, "executable_sha256": hashlib.sha256(Path(cli).read_bytes()).hexdigest(),
                            "model": "gpt-5.6-luna", "effort": "low", "attempts": 1,
                            "image": False, "tools": False, "authority_granted": False}
            try:
                args = [cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                        "--sandbox", "read-only", "--skip-git-repo-check", "--json",
                        "--model", "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"',
                        "-c", "project_doc_max_bytes=0", "--output-schema",
                        map_path(req["schema"], repo), "-C", map_path(req["working"], repo), "-"]
                argv_capture["argv"] = [Path(cli).name] + args[1:-1] + ["<stdin>"]
                completed = subprocess.run(args, input=req["prompt"] + "\n", text=True,
                                           encoding="utf-8", errors="replace", capture_output=True,
                                           timeout=timeout, check=False)
                response = completed.stdout or ""
                broker = {"request_id": rid, "returncode": completed.returncode,
                          "stderr": (completed.stderr or "")[-2000:],
                          "boundary": "local-host-Codex-CLI", "authority_granted": False,
                          "started_ns": started, "exited_ns": time.perf_counter_ns()}
            except Exception as exc:
                response = ""
                broker = {"request_id": rid, "returncode": None,
                          "error_class": type(exc).__name__, "error": str(exc)[:1000],
                          "boundary": "local-host-Codex-CLI", "authority_granted": False,
                          "started_ns": started, "exited_ns": time.perf_counter_ns()}
            (ipc / f"{rid}.response.jsonl").write_text(response, encoding="utf-8")
            (ipc / f"{rid}.broker.json").write_text(json.dumps(broker) + "\n", encoding="utf-8")
            (ipc / f"{rid}.argv.json").write_text(json.dumps(argv_capture) + "\n", encoding="utf-8")
            return 0 if broker.get("returncode") == 0 else 1
        time.sleep(.05)


if __name__ == "__main__":
    ipc = Path(os.environ["HOST_MODEL_IPC_DIR"]).resolve()
    repo = Path(os.environ["REPO_DIR"]).resolve()
    raise SystemExit(serve(ipc, repo))
