#!/usr/bin/env python3
"""One-shot local heartbeat trace capture for Issue #5531 A01."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import platform


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "a01"
ALLOCATION = "FAILURE-DETECTOR-5531-REGIME-TRACE-A01-20261005-01"
THRESHOLD_PCT = 50.0


class FILETIME(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    def as_int(self) -> int:
        return (int(self.high) << 32) | int(self.low)


def get_system_times() -> tuple[int, int, int]:
    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    ok = ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    )
    if not ok:
        raise ctypes.WinError()
    return idle.as_int(), kernel.as_int(), user.as_int()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def child(nonce: str, duration_s: float, period_ms: float, allocation: str) -> int:
    period_ns = int(period_ms * 1_000_000)
    start = time.perf_counter_ns()
    end = start + int(duration_s * 1_000_000_000)
    seq = 0
    while True:
        now = time.perf_counter_ns()
        if now >= end:
            break
        print(json.dumps({
            "event": "heartbeat",
            "allocation": allocation,
            "pid": os.getpid(),
            "nonce": nonce,
            "sequence": seq,
            "worker_monotonic_ns": now,
        }, separators=(",", ":")), flush=True)
        if seq % 10 == 0:
            print(json.dumps({
                "event": "progress",
                "allocation": allocation,
                "pid": os.getpid(),
                "nonce": nonce,
                "progress_sequence": seq // 10,
                "worker_monotonic_ns": time.perf_counter_ns(),
            }, separators=(",", ":")), flush=True)
        seq += 1
        target = start + seq * period_ns
        delay_ns = target - time.perf_counter_ns()
        if delay_ns > 0:
            time.sleep(delay_ns / 1_000_000_000)
    return 0


def collect(duration_s: int, period_ms: int, out: Path, allocation: str) -> int:
    if os.name != "nt":
        raise RuntimeError("A01 requires Windows GetSystemTimes")
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing output: {out}")
    if allocation == ALLOCATION and not (ROOT / "FREEZE.json").is_file():
        raise RuntimeError("formal allocation requires committed FREEZE.json")
    out.mkdir(parents=True)
    nonce = secrets.token_hex(16)
    started_utc = datetime.now(timezone.utc).isoformat()
    started_mono = time.perf_counter_ns()
    host_samples: list[dict[str, object]] = []
    sensor_error: list[str] = []
    stop_sensor = threading.Event()
    previous = get_system_times()

    def sensor() -> None:
        nonlocal previous
        sample_seq = 0
        while not stop_sensor.wait(1.0):
            try:
                current = get_system_times()
                dt = sum(current[i] - previous[i] for i in range(3))
                idle = current[0] - previous[0]
                if dt <= 0 or idle < 0 or idle > dt:
                    raise RuntimeError("invalid Windows system-time delta")
                busy = 100.0 * (dt - idle) / dt
                stamp = time.perf_counter_ns()
                host_samples.append({
                    "sequence": sample_seq,
                    "observer_monotonic_ns": stamp,
                    "busy_pct": round(busy, 6),
                    "regime": "elevated" if busy >= THRESHOLD_PCT else "ordinary",
                    "threshold_pct": THRESHOLD_PCT,
                })
                sample_seq += 1
                previous = current
            except Exception as exc:  # retain sensor failure; never repair/retry
                sensor_error.append(f"{type(exc).__name__}: {exc}")
                stop_sensor.set()

    sensor_thread = threading.Thread(target=sensor, name="host-cpu-sensor", daemon=True)
    sensor_thread.start()
    time.sleep(0.1)  # allow the first external host-counter interval to begin
    child_started_utc = datetime.now(timezone.utc).isoformat()
    cmd = [sys.executable, "-u", str(Path(__file__).resolve()), "--worker",
           nonce, str(duration_s), str(period_ms), allocation]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=False, bufsize=-1, cwd=str(ROOT))
    candidate_pid = proc.pid
    raw_path = out / "heartbeats.jsonl"
    progress_path = out / "progress.jsonl"
    source_stdout_path = out / "worker-stdout.jsonl"
    observed_path = out / "observed-events.jsonl"
    arrivals = 0
    progress_count = 0
    malformed = []
    parent_deadline = time.perf_counter_ns() + int((duration_s + 20) * 1_000_000_000)
    try:
        assert proc.stdout is not None
        with raw_path.open("x", encoding="utf-8", newline="\n") as heartbeats, \
             progress_path.open("x", encoding="utf-8", newline="\n") as progress, \
             source_stdout_path.open("xb") as source_stdout, \
             observed_path.open("x", encoding="utf-8", newline="\n") as observed:
            for raw_line in proc.stdout:
                source_stdout.write(raw_line)
                source_stdout.flush()
                arrival_ns = time.perf_counter_ns()
                try:
                    line = raw_line.decode("utf-8")
                    event = json.loads(line)
                    event["observer_received_monotonic_ns"] = arrival_ns
                    observed.write(json.dumps(event, sort_keys=True) + "\n")
                    observed.flush()
                    if event.get("event") == "heartbeat":
                        heartbeats.write(json.dumps(event, sort_keys=True) + "\n")
                        arrivals += 1
                    elif event.get("event") == "progress":
                        progress.write(json.dumps(event, sort_keys=True) + "\n")
                        progress_count += 1
                    else:
                        malformed.append("unknown event type")
                except Exception as exc:
                    malformed.append(f"{type(exc).__name__}: {exc}")
                if arrival_ns > parent_deadline:
                    proc.kill()
                    malformed.append("parent deadline exceeded")
                    break
        stdout_tail, stderr = proc.communicate(timeout=10)
    except Exception as exc:
        if proc.poll() is None:
            proc.kill()
        try:
            stdout_tail, stderr = proc.communicate(timeout=10)
        except Exception:
            stdout_tail, stderr = "", "child stream collection failed"
        malformed.append(f"collector exception: {type(exc).__name__}: {exc}")
    finally:
        stop_sensor.set()
        sensor_thread.join(timeout=3)

    finished_mono = time.perf_counter_ns()
    finished_utc = datetime.now(timezone.utc).isoformat()
    (out / "candidate.stdout-tail.txt").write_bytes(stdout_tail or b"")
    (out / "candidate.stderr.txt").write_bytes(stderr or b"")
    with (out / "host_cpu.jsonl").open("x", encoding="utf-8", newline="\n") as f:
        for row in host_samples:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    freeze_path = ROOT / "FREEZE.json"
    run = {
        "schema": "failure-detector-5531-regime-trace-run-v1",
        "allocation": allocation,
        "candidate_command": ["python", "-B", "collect.py", "--duration-seconds",
                              duration_s, "--period-ms", period_ms],
        "candidate_exit_code": proc.returncode,
        "retry_count": 0,
        "worker_pid": candidate_pid,
        "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
        "freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest() if freeze_path.is_file() else None,
        "started_utc": started_utc,
        "child_started_utc": child_started_utc,
        "ended_utc": finished_utc,
        "started_monotonic_ns": started_mono,
        "ended_monotonic_ns": finished_mono,
        "host": platform.platform(),
        "python": sys.version,
        "duration_seconds": duration_s,
        "period_ms": period_ms,
        "host_counter": "Windows GetSystemTimes, sampled by observer thread at ~1Hz",
        "host_regime_threshold_pct": THRESHOLD_PCT,
        "heartbeat_rows": arrivals,
        "progress_rows": progress_count,
        "host_sample_rows": len(host_samples),
        "sensor_errors": sensor_error,
        "malformed_records": malformed,
        "capture_status": "CAPTURED" if proc.returncode == 0 and not sensor_error and not malformed else "FAIL_CAPTURE",
        "interpretation": "controlled healthy local process only; no detector-performance inference",
    }
    write_json(out / "RUN.json", run)
    manifest_lines = []
    for path in sorted(out.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name not in {"OUTPUT_SHA256SUMS.txt", "AUDIT.json"}:
            manifest_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (out / "OUTPUT_SHA256SUMS.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(json.dumps({k: run[k] for k in ("candidate_exit_code", "heartbeat_rows",
        "progress_rows", "host_sample_rows", "capture_status")}, sort_keys=True))
    return 0 if run["capture_status"] == "CAPTURED" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-seconds", type=int, default=600)
    parser.add_argument("--period-ms", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--allocation-id", default=ALLOCATION)
    parser.add_argument("--worker", nargs=4, metavar=("NONCE", "DURATION", "PERIOD", "ALLOCATION"))
    args = parser.parse_args()
    if args.worker:
        nonce, duration, period, allocation = args.worker
        return child(nonce, float(duration), float(period), allocation)
    return collect(args.duration_seconds, args.period_ms, args.output_dir, args.allocation_id)


if __name__ == "__main__":
    raise SystemExit(main())
