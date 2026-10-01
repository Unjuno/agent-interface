#!/usr/bin/env python3
"""WSL2 host orchestration; uses the exact production bounded JSON client."""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
import tempfile
import traceback
import uuid


MAIN = "f7d5cc8535995db0c36dd85d4b71877503bd0db8"
IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
IMAGE = IMAGE_ID
LEASE_SHA256 = "E71F9850D3999A31FCB86C00F9EF7A8BA19BAE8D3A8BDC11BF7BD620817A535F"
EXCHANGE_SHA256 = "DECB19099C686EE494FE307C3BF411E61C59E05470319AB80159147D2BD73DE3"
NS = 1_000_000_000


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_exchange(path):
    spec = importlib.util.spec_from_file_location("pinned_production_exchange", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.exchange


def append_jsonl(path, obj):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, sort_keys=True, separators=(",", ":"))+"\n")
        stream.flush()
        os.fsync(stream.fileno())


def mount_arg(source, target, readonly=False):
    value = f"type=bind,source={source},target={target}"
    return value + (",readonly" if readonly else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--construction-only", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    source = args.source.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lease_path = repo/"research/live_control/lease.py"
    exchange_path = repo/"research/live_control/unix_json_deadline.py"
    result = {"schema": "issue3886_desktop_wsl_construction_v1",
              "main": MAIN, "docker_image": IMAGE, "docker_image_id": IMAGE_ID,
              "lease_sha256": sha(lease_path),
              "exchange_sha256": sha(exchange_path),
              "host_platform": sys.platform,
              "host_python": sys.version,
              "host_uname": platform.uname()._asdict(),
              "host_clock": "time.perf_counter_ns",
              "construction_only": args.construction_only,
              "formal_sessions": 0, "status": "INCOMPLETE"}
    result["docker_context"] = subprocess.run(
        ["docker", "context", "show"], capture_output=True, text=True,
        timeout=10).stdout.strip()
    result["docker_engine"] = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],
        capture_output=True, text=True, timeout=10).stdout.strip()
    exchange = load_exchange(exchange_path)
    container_id = None
    container_name = f"issue3886-{uuid.uuid4().hex[:12]}"
    socket_dir = Path(tempfile.mkdtemp(prefix="issue3886-socket-"))
    socket_path = socket_dir/"clock.sock"
    log = (out/"docker.stdout.log").open("w", encoding="utf-8")
    try:
        cmd = ["docker", "run", "--detach", "--name", container_name,
               "--pull=never",
               "--platform", "linux/amd64", "--network", "none", "--read-only",
               "--user", f"{os.getuid()}:{os.getgid()}",
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
               "--mount", mount_arg(source, "/src", True),
               "--mount", mount_arg(lease_path, "/pinned/lease.py", True),
               "--mount", mount_arg(socket_dir, "/socket"),
               "--mount", mount_arg(out, "/evidence"),
               IMAGE, "python", "/src/container_server.py",
               "--socket", "/socket/clock.sock",
               "--ready", "/evidence/server-ready.json",
               "--journal", "/evidence/server.jsonl",
               "--lease-source", "/pinned/lease.py"]
        started = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        result["docker_run_returncode"] = started.returncode
        result["docker_run_stdout"] = started.stdout.strip()
        result["docker_run_stderr"] = started.stderr[-4000:]
        if started.returncode != 0:
            result["status"] = "HOLD_SOCKET_UNAVAILABLE"
            return
        container_id = started.stdout.strip()
        result["container_id"] = container_id
        result["server_socket_visible_to_host"] = False
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            if (out/"server-ready.json").exists():
                result["container_ready"] = json.loads((out/"server-ready.json").read_text())
                result["server_socket_visible_to_host"] = socket_path.exists()
                break
            time.sleep(0.05)
        if not result["server_socket_visible_to_host"]:
            result["status"] = "HOLD_SOCKET_UNAVAILABLE"
            return

        request_id = str(uuid.uuid4())
        h1 = time.perf_counter_ns()
        response = exchange(socket_path,
                            {"kind": "clock", "request_id": request_id,
                             "host_send_ns": h1}, timeout=2)
        h4 = time.perf_counter_ns()
        result.update({"status": "PASS_CONSTRUCTION_SOCKET_JSON_LEASE_RUNTIME",
                       "sample": {"request_id": request_id,
                                  "host_send_ns": h1,
                                  "container_receive_ns": response["container_receive_ns"],
                                  "container_send_ns": response["container_send_ns"],
                                  "host_receive_ns": h4,
                                  "offset_interval_ns": [response["container_send_ns"]-h4,
                                                         response["container_receive_ns"]-h1],
                                  "rtt_ns": h4-h1}})
        append_jsonl(out/"host.jsonl", {"host_send_ns": h1,
                                        "host_receive_ns": h4,
                                        "response": response})
    except Exception as exc:
        result.update({"status": "HOLD_SOCKET_UNAVAILABLE",
                       "exception": repr(exc),
                       "traceback": traceback.format_exc()})
    finally:
        if container_id:
            logs = subprocess.run(["docker", "logs", container_id],
                                  capture_output=True, text=True, timeout=10)
            result["container_logs_stdout"] = logs.stdout[-8000:]
            result["container_logs_stderr"] = logs.stderr[-8000:]
            inspected_before = subprocess.run(["docker", "inspect", container_id,
                                               "--format", "{{.State.Status}} {{.State.ExitCode}}"],
                                              capture_output=True, text=True, timeout=10)
            result["container_state_before_cleanup"] = inspected_before.stdout.strip()
            stopped = subprocess.run(["docker", "stop", "--timeout", "2", container_id],
                                      capture_output=True, text=True, timeout=10)
            result["docker_stop_returncode"] = stopped.returncode
            result["docker_stop_stdout"] = stopped.stdout.strip()
            result["docker_stop_stderr"] = stopped.stderr[-2000:]
            removed = subprocess.run(["docker", "rm", "-f", container_id],
                                      capture_output=True, text=True, timeout=10)
            result["docker_rm_returncode"] = removed.returncode
            result["docker_rm_stderr"] = removed.stderr[-2000:]
            inspected = subprocess.run(["docker", "inspect", container_id,
                                        "--format", "{{.State.Status}}"],
                                       capture_output=True, text=True, timeout=10)
            result["container_terminal_state"] = "removed" if inspected.returncode != 0 else inspected.stdout.strip()
        log.close()
        try:
            socket_dir.rmdir()
        except OSError:
            pass
        (out/"result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                                       encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
