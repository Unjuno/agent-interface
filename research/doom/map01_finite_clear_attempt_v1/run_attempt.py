"""Bounded controller-visible MAP01 attempt for Issue #2679.

This is deliberately a finite transport/control allocation. It does not use
privileged game state or claim that scripted movement is model competence.
The raw session output is retained for independent terminal classification.
"""
from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=2679)
    ap.add_argument("--skill", type=int, default=1)
    ap.add_argument("--timeout-seconds", type=int, default=60)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.out / "runtime"
    cmd = [
        sys.executable,
        str(Path(__file__).with_name("session_map01_v13.py")),
        "--out", str(runtime), "--seed", str(args.seed),
        "--timeout-seconds", str(args.timeout_seconds), "--skill", str(args.skill),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    events: list[dict] = []
    q: queue.Queue[dict | None] = queue.Queue()

    def read_stdout() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            try:
                q.put(json.loads(line))
            except json.JSONDecodeError:
                q.put({"event": "malformed_stdout", "line": line.rstrip()})
        q.put(None)

    import threading
    threading.Thread(target=read_stdout, daemon=True).start()

    def wait_for(predicate, limit: float = 20.0) -> dict:
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            row = q.get(timeout=max(0.1, deadline - time.monotonic()))
            if row is None:
                raise RuntimeError("session stdout closed")
            events.append(row)
            if predicate(row):
                return row
        raise TimeoutError("session event timeout")

    def send(row: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(row) + "\n")
        proc.stdin.flush()

    ready = None
    initial = None
    failure = None
    try:
        ready = wait_for(lambda r: r.get("event") == "ready")
        initial = wait_for(lambda r: r.get("event") == "observation" and r.get("id") == "initial")
        latest = initial
        # Fixed, bounded movement/fire batches exercise real OS input and release.
        # They are an intentionally weak baseline, not a model-in-loop claim.
        for index in range(12):
            clock = send_and_wait(send, wait_for, {"op": "clock"}, lambda r: r.get("event") == "clock")
            send({
                "op": "submit", "id": f"finite-baseline-{index}",
                "expected_sequence": latest["sequence"],
                "valid_until_ns": clock["runtime_ns"] + 5_000_000_000,
                "steps": [
                    {"op": "hold", "keys": ["w", "Shift_L"], "duration_ms": 700},
                    {"op": "hold", "keys": ["space"], "duration_ms": 250},
                    {"op": "observe"},
                ],
            })
            terminal = wait_for(lambda r, ident=f"finite-baseline-{index}":
                                r.get("event") == "terminal" and r.get("id") == ident,
                                limit=15.0)
            if terminal.get("status") != "completed":
                break
            for row in reversed(events):
                if row.get("event") == "observation":
                    latest = row
                    break
        send({"op": "finish"})
        wait_for(lambda r: r.get("event") == "post_control_score", limit=15.0)
        proc.stdin.close()
        proc.wait(timeout=15)
    except Exception as exc:
        failure = repr(exc)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    stderr_text = proc.stderr.read() if proc.stderr is not None else ""
    (args.out / "controller-events.json").write_text(
        json.dumps(events, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "allocation.json").write_text(json.dumps({
        "allocation_id": "map01-finite-clear-attempt-v1",
        "seed": args.seed, "skill": args.skill,
        "timeout_seconds": args.timeout_seconds,
        "controller": "fixed bounded OS-input baseline; no model call",
        "ready": ready, "initial": initial,
        "event_count": len(events), "process_returncode": proc.returncode,
        "failure": failure, "session_stderr": stderr_text,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failure:
        print(json.dumps({"failure": failure, "session_stderr": stderr_text}, sort_keys=True), file=sys.stderr)
        return 2
    return 0


def send_and_wait(send, wait_for, row, predicate):
    send(row)
    return wait_for(predicate)


if __name__ == "__main__":
    raise SystemExit(main())
