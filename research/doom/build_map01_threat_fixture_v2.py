"""Derive a second real MAP01 threat fixture from a hash-bound parent fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
from map01_overlap_controller_v31 import compile_commands


CONTINUATION = [
    {"kind": "commands", "commands": [
        {"action": "strafe_left", "extent": "short"},
        {"action": "retreat_fire", "extent": "short"},
        {"action": "strafe_right", "extent": "short"},
    ]},
    {"kind": "coast", "duration_ms": 750},
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coast_steps(duration_ms):
    steps = []
    while duration_ms:
        part = min(5000, duration_ms)
        steps.append({"op": "coast", "duration_ms": part, "sample_ms": 250})
        duration_ms -= part
    return steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fixture-out", type=Path, required=True)
    parser.add_argument("--parent-manifest", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=990619)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    parent = args.parent_manifest.resolve()
    plan = {
        "schema": "map01_threat_fixture_continuation_v2",
        "seed": args.seed,
        "parent_manifest": str(parent),
        "parent_manifest_sha256": sha256(parent),
        "basis": "one frozen model-free continuation outside the exact v1 fixture state",
        "input_path": "session v8 X11 Executor only",
        "steps": CONTINUATION,
    }
    (args.out / "continuation.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, str(HERE / "session_map01_v8.py"),
        "--out", str(args.out / "runtime"), "--seed", str(args.seed),
        "--load-fixture-manifest", str(parent),
        "--fixture-out", str(args.fixture_out),
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
       text=True, bufsize=1)
    incoming = queue.Queue()
    events = []

    def reader():
        for line in process.stdout:
            row = json.loads(line)
            events.append(row)
            incoming.put(row)

    threading.Thread(target=reader, daemon=True).start()
    latest = None

    def wait(predicate, timeout=45):
        nonlocal latest
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                row = incoming.get(timeout=min(.25, deadline - time.monotonic()))
            except queue.Empty:
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read())
                continue
            if row.get("event") == "observation":
                latest = row
            if predicate(row):
                return row
        raise TimeoutError("fixture continuation event timeout")

    def send(command):
        process.stdin.write(json.dumps(command) + "\n")
        process.stdin.flush()

    saved = None
    try:
        ready = wait(lambda row: row.get("event") == "ready")
        if ready.get("fixture") is None:
            raise RuntimeError("parent fixture was not loaded")
        latest = wait(lambda row: row.get("event") == "observation")
        for index, step in enumerate(CONTINUATION):
            identifier = f"fixture-continuation-{index}"
            program = (coast_steps(step["duration_ms"]) if step["kind"] == "coast"
                       else compile_commands(step["commands"]))
            send({"op": "submit", "id": identifier,
                  "expected_sequence": latest["sequence"],
                  "valid_until_ns": time.perf_counter_ns() + 15_000_000_000,
                  "steps": program})
            accepted = wait(lambda row: row.get("event") in ("accepted", "rejected") and
                            (row.get("id") == identifier or row.get("event") == "rejected"))
            if accepted["event"] != "accepted":
                raise RuntimeError(accepted)
            terminal = wait(lambda row: row.get("event") == "terminal" and
                            row.get("id") == identifier)
            release = terminal.get("release", {})
            if (terminal.get("status") != "completed" or release.get("verified") is not True or
                    release.get("buttons_down") != [] or release.get("keys_down") != []):
                raise RuntimeError("continuation program did not verify empty release")
        send({"op": "save_fixture"})
        saved = wait(lambda row: row.get("event") == "fixture_saved")
        process.wait(timeout=20)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        (args.out / "stderr.txt").write_text(process.stderr.read())
    summary = {
        "schema": "map01_threat_fixture_continuation_report_v2",
        "passed": True,
        "fixture": saved["save"],
        "fixture_manifest": saved["manifest"],
        "fixture_sha256": saved["save_sha256"],
        "episode_tic": saved["episode_tic"],
        "source_sequence": saved["source_sequence"],
        "programs": len(CONTINUATION),
        "verified_releases": sum(
            row.get("event") == "terminal" and row.get("release", {}).get("verified")
            for row in events),
        "model_calls": 0,
        "parent_manifest_sha256": sha256(parent),
    }
    (args.out / "report.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
