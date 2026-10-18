from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import stat
import sys
import threading
import time
from ctypes import wintypes


def wait_readable(fd: int, timeout_s: float, quantum_s: float) -> bool:
    if stat.S_ISREG(os.fstat(fd).st_mode):
        return True
    import msvcrt

    handle = msvcrt.get_osfhandle(fd)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    peek = kernel32.PeekNamedPipe
    peek.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p,
                     ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p)
    peek.restype = wintypes.BOOL
    deadline = time.monotonic() + max(0.0, timeout_s)
    while True:
        available = wintypes.DWORD()
        if peek(handle, None, 0, None, ctypes.byref(available), None):
            if available.value:
                return True
        else:
            error = ctypes.get_last_error()
            if error == 109:
                return True
            raise OSError(error, ctypes.FormatError(error))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(remaining, quantum_s))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure_latency(arm: str, quantum_s: float, pair: int, delay_ms: int, rng: random.Random) -> dict:
    read_fd, write_fd = os.pipe()
    state = {}
    delay_s = delay_ms / 1000.0

    def writer():
        time.sleep(delay_s)
        state["write_start_ns"] = time.perf_counter_ns()
        os.write(write_fd, bytes([pair % 251 + 1]))
        os.close(write_fd)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    try:
        if not wait_readable(read_fd, 2.0, quantum_s):
            raise RuntimeError(f"pipe readiness timeout: {arm} pair {pair}")
        ready_ns = time.perf_counter_ns()
        payload = os.read(read_fd, 8)
        thread.join(timeout=1.0)
        if thread.is_alive():
            raise RuntimeError("writer thread did not finish")
        expected = bytes([pair % 251 + 1])
        if payload != expected:
            raise RuntimeError(f"pipe payload mismatch: {arm} pair {pair}")
        return {
            "kind": "latency", "pair": pair, "arm": arm, "quantum_ms": quantum_s * 1000,
            "delay_ms": delay_ms, "write_start_ns": state["write_start_ns"],
            "ready_ns": ready_ns, "latency_ms": (ready_ns - state["write_start_ns"]) / 1e6,
            "payload_ok": True,
        }
    finally:
        os.close(read_fd)
        if thread.is_alive():
            thread.join(timeout=1.0)


def measure_idle(arm: str, quantum_s: float, trials: int) -> list[dict]:
    rows = []
    timeout_s = 0.02857
    for i in range(trials):
        read_fd, write_fd = os.pipe()
        cpu_start, wall_start = time.process_time_ns(), time.perf_counter_ns()
        timed_out = not wait_readable(read_fd, timeout_s, quantum_s)
        wall_end, cpu_end = time.perf_counter_ns(), time.process_time_ns()
        os.close(write_fd)
        os.close(read_fd)
        rows.append({
            "kind": "idle", "pair": i, "arm": arm, "quantum_ms": quantum_s * 1000,
            "timeout_ms": timeout_s * 1000, "wall_ms": (wall_end-wall_start)/1e6,
            "cpu_ms": (cpu_end-cpu_start)/1e6, "timed_out": timed_out,
        })
    return rows


def smoke_eof(quantum_s: float) -> bool:
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    try:
        return wait_readable(read_fd, 0.5, quantum_s) and os.read(read_fd, 1) == b""
    finally:
        os.close(read_fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("This construction requires native Windows.")
    args.out.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve()
    rng = random.Random(590104)
    delays = [rng.randint(2, 12) for _ in range(128)]
    smoke = {"1ms_eof": smoke_eof(.001), "5ms_eof": smoke_eof(.005)}
    if not all(smoke.values()):
        raise RuntimeError("EOF readiness smoke test failed")
    rows = []
    for pair, delay in enumerate(delays):
        arms = [("1ms", .001), ("5ms", .005)]
        rng.shuffle(arms)
        for arm, quantum in arms:
            rows.append(measure_latency(arm, quantum, pair, delay, rng))
    idle_arms = [("1ms", .001), ("5ms", .005)]
    rng.shuffle(idle_arms)
    for arm, quantum in idle_arms:
        rows.extend(measure_idle(arm, quantum, 70))
    csv_path = args.out / "raw.csv"
    fields = list(dict.fromkeys(key for row in rows for key in row))
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "record_id": "windows_pipe_quantum_59_t1_20261004",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "candidate_source_sha256": sha256(source_path),
        "raw_csv_sha256": sha256(csv_path),
        "row_count": len(rows),
        "eof_smoke": smoke,
        "user_path_redacted": True,
    }
    (args.out / "machine.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "candidate_sha256": result["candidate_source_sha256"], "platform": result["platform"], "python": result["python"]}))

if __name__ == "__main__":
    main()



