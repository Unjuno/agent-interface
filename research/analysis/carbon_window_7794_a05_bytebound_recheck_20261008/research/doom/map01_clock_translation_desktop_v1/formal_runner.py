#!/usr/bin/env python3
"""One fixed Docker Desktop/WSL2 clock-and-Lease allocation; do not rerun."""
import argparse
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

from host_runner import (EXCHANGE_SHA256, IMAGE, IMAGE_ID, LEASE_SHA256,
                         MAIN, NS, append_jsonl, load_exchange, mount_arg, sha)


def exchange_record(exchange, socket_path, request, client_journal):
    h1 = time.perf_counter_ns()
    response = exchange(socket_path, {**request, "host_send_ns": h1}, timeout=3)
    h4 = time.perf_counter_ns()
    c2 = response["container_receive_ns"]
    c3 = response["container_send_ns"]
    row = {"request": request, "response": response,
           "host_send_ns": h1, "host_receive_ns": h4,
           "lower_offset_ns": c3-h4, "upper_offset_ns": c2-h1,
           "rtt_ns": h4-h1}
    if row["lower_offset_ns"] > row["upper_offset_ns"]:
        row["interval_valid"] = False
    else:
        row["interval_valid"] = True
    append_jsonl(client_journal, row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--cadence-seconds", type=float, default=5.0)
    ap.add_argument("--sample-count", type=int, default=120)
    args = ap.parse_args()
    repo, source, out = args.repo.resolve(), args.source.resolve(), args.out.resolve()
    if args.sample_count != 120 or args.cadence_seconds != 5.0:
        raise SystemExit("formal constants are frozen at 120 samples and 5.0 seconds")
    out.mkdir(parents=True, exist_ok=False)
    socket_dir = Path(__import__("tempfile").mkdtemp(prefix="issue3886-formal-socket-"))
    socket_path = socket_dir/"clock.sock"
    lease_path = repo/"research/live_control/lease.py"
    exchange_path = repo/"research/live_control/unix_json_deadline.py"
    exchange = load_exchange(exchange_path)
    manifest_path = source/"SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = {"schema": "issue3886_desktop_wsl_formal_v1",
              "allocation": "issue3886-desktop-wsl-clock-v1",
              "main": MAIN, "docker_image": IMAGE, "docker_image_id_expected": IMAGE_ID,
              "lease_sha256": sha(lease_path), "exchange_sha256": sha(exchange_path),
              "source_manifest_sha256": sha(manifest_path),
              "host_platform": sys.platform, "host_clock": "time.perf_counter_ns",
              "host_python": sys.version, "host_uname": platform.uname()._asdict(),
              "sample_count_expected": 120, "cadence_target_ns": 5*NS,
              "status": "INCOMPLETE", "formal_invocations": 1, "reruns": 0}
    allocation_hashes = {name: sha(source/name)
                         for name in manifest["allocation_sources"]}
    result["allocation_source_hashes"] = allocation_hashes
    if allocation_hashes != manifest["allocation_sources"]:
        result["status"] = "HOLD_SOURCE_HASH"
        result["source_manifest_expected"] = manifest["allocation_sources"]
        out.joinpath("result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)
        return
    result["docker_context"] = subprocess.run(
        ["docker", "context", "show"], capture_output=True, text=True,
        timeout=10).stdout.strip()
    result["docker_engine"] = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],
        capture_output=True, text=True, timeout=10).stdout.strip()
    name = f"issue3886-formal-{uuid.uuid4().hex[:12]}"
    cid = None
    try:
        inspect = subprocess.run(["docker", "image", "inspect", IMAGE,
                                  "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                                 text=True, capture_output=True, timeout=15)
        result["image_inspect"] = inspect.stdout.strip()
        if inspect.returncode != 0 or IMAGE_ID not in inspect.stdout or "linux/amd64" not in inspect.stdout:
            result["status"] = "HOLD_IMAGE_IDENTITY"
            return
        cmd = ["docker", "run", "--detach", "--name", name,
               "--pull=never", "--platform", "linux/amd64", "--network", "none",
               "--read-only", "--user", f"{os.getuid()}:{os.getgid()}",
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
               "--mount", mount_arg(source, "/src", True),
               "--mount", mount_arg(lease_path, "/pinned/lease.py", True),
               "--mount", mount_arg(socket_dir, "/socket"),
               "--mount", mount_arg(out, "/evidence"), IMAGE,
               "python", "/src/container_server.py",
               "--socket", "/socket/clock.sock",
               "--ready", "/evidence/server-ready.json",
               "--journal", "/evidence/server.jsonl",
               "--lease-source", "/pinned/lease.py"]
        started = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        result["docker_run_returncode"] = started.returncode
        result["docker_run_stdout"] = started.stdout.strip()
        result["docker_run_stderr"] = started.stderr[-4000:]
        if started.returncode != 0:
            result["status"] = "HOLD_SOCKET_UNAVAILABLE"
            return
        cid = started.stdout.strip()
        result["container_id"] = cid
        ready_deadline = time.monotonic()+15
        while time.monotonic() < ready_deadline:
            if (out/"server-ready.json").exists() and socket_path.exists():
                result["container_ready"] = json.loads((out/"server-ready.json").read_text())
                break
            time.sleep(0.05)
        else:
            result["status"] = "HOLD_SOCKET_UNAVAILABLE"
            return

        client_journal = out/"host.jsonl"
        sample_rows = []
        start = time.perf_counter_ns()
        for index in range(120):
            due = start + index*5*NS
            remaining = due-time.perf_counter_ns()
            if remaining > 0:
                time.sleep(remaining/NS)
            row = exchange_record(exchange, socket_path,
                                  {"kind": "clock", "sample_index": index,
                                   "request_id": str(uuid.uuid4())}, client_journal)
            row["sample_index"] = index
            row["scheduled_elapsed_ns"] = time.perf_counter_ns()-start
            append_jsonl(out/"samples.jsonl", row)
            sample_rows.append(row)
            if not row["interval_valid"] or row["upper_offset_ns"]-row["lower_offset_ns"] > 250_000_000:
                result["status"] = "HOLD_CLOCK_BOUND_UNSTABLE"
                result["stop_sample_index"] = index
                return

        common_low = max(row["lower_offset_ns"] for row in sample_rows)
        common_high = min(row["upper_offset_ns"] for row in sample_rows)
        result["offset_common_intersection_ns"] = [common_low, common_high]
        if common_low > common_high:
            result["status"] = "HOLD_CLOCK_BOUND_UNSTABLE"
            return
        offset = common_low
        result["conservative_offset_ns"] = offset
        result["sample_count"] = len(sample_rows)
        result["max_interval_width_ns"] = max(
            row["upper_offset_ns"]-row["lower_offset_ns"] for row in sample_rows)
        result["max_rtt_ns"] = max(row["rtt_ns"] for row in sample_rows)

        controls = [("translated_live_25s", 25*NS, 0),
                    ("expired", -1*NS, 0),
                    ("over_horizon_31s", 31*NS, 0),
                    ("delayed_750ms_with_500ms_auth", 500_000_000, 750_000_000)]
        control_rows = []
        for control_name, host_delta, delay_ns in controls:
            host_now = time.perf_counter_ns()
            host_deadline = host_now+host_delta
            deadline = host_deadline+offset
            row = exchange_record(exchange, socket_path,
                                  {"kind": "lease", "control": control_name,
                                   "request_id": str(uuid.uuid4()),
                                   "host_deadline_ns": host_deadline,
                                   "deadline_ns": deadline,
                                   "offset_lower_ns": offset,
                                   "host_authorized_remaining_at_send_ns": host_deadline-time.perf_counter_ns(),
                                   "delay_ns": delay_ns}, client_journal)
            row["control"] = control_name
            row["host_deadline_ns"] = host_deadline
            row["deadline_ns"] = deadline
            row["host_delta_ns"] = host_delta
            append_jsonl(out/"controls.jsonl", row)
            control_rows.append(row)
        result["control_decisions"] = [
            {"control": row["control"], "decision": row["response"].get("decision"),
             "validation_start_ns": row["response"].get("validation_start_ns"),
             "validation_end_ns": row["response"].get("validation_end_ns"),
             "remaining_ns": row["response"].get("remaining_ns")}
            for row in control_rows]

        shutdown = exchange_record(exchange, socket_path,
                                  {"kind": "shutdown", "request_id": str(uuid.uuid4())},
                                  client_journal)
        result["shutdown_receipt"] = shutdown
        wait = subprocess.run(["docker", "wait", cid], text=True,
                              capture_output=True, timeout=15)
        result["container_wait_returncode"] = wait.returncode
        result["container_exit_code"] = wait.stdout.strip()
        result["status"] = "FORMAL_COMPLETE_PENDING_INDEPENDENT_AUDIT"
    except Exception as exc:
        result.update({"status": "STOP_EXCEPTION",
                       "exception": repr(exc),
                       "traceback": traceback.format_exc()})
    finally:
        if cid:
            logs = subprocess.run(["docker", "logs", cid], text=True,
                                  capture_output=True, timeout=10)
            result["container_logs_stdout"] = logs.stdout[-5000:]
            result["container_logs_stderr"] = logs.stderr[-5000:]
            inspect_state = subprocess.run(["docker", "inspect", cid, "--format",
                                            "{{.State.Status}} {{.State.ExitCode}}"],
                                           text=True, capture_output=True, timeout=10)
            result["container_terminal_receipt"] = inspect_state.stdout.strip()
            rm = subprocess.run(["docker", "rm", "-f", cid], text=True,
                                capture_output=True, timeout=10)
            result["docker_rm_returncode"] = rm.returncode
        (out/"result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                                       encoding="utf-8")
        try:
            socket_dir.rmdir()
        except OSError:
            pass
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
