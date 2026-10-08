"""Build a real MAP01 contact fixture through recorded X11/OS-input programs."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
from map01_overlap_controller_v26 import compile_commands


PRELUDE = [
    {"kind": "coast", "duration_ms": 9768},
    {"kind": "commands", "commands": [{"action": "forward", "extent": "medium"}]},
    {"kind": "coast", "duration_ms": 9674},
    {"kind": "commands", "commands": [
        {"action": "forward", "extent": "short"}, {"action": "use", "extent": "pulse"}]},
    {"kind": "coast", "duration_ms": 9476},
    {"kind": "commands", "commands": [
        {"action": "use", "extent": "pulse"}, {"action": "forward", "extent": "short"}]},
    {"kind": "coast", "duration_ms": 500},
]


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
    parser.add_argument("--seed", type=int, default=990619)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "map01_threat_fixture_prelude_v1", "seed": args.seed,
            "basis": "v23 decisions 0-2 and their measured model-wall coast intervals",
            "input_path": "session v7 X11 Executor only", "steps": PRELUDE}
    (args.out / "prelude.json").write_text(json.dumps(plan, indent=2) + "\n")

    process = subprocess.Popen([
        sys.executable, str(HERE / "session_map01_v7.py"),
        "--out", str(args.out / "runtime"), "--seed", str(args.seed),
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
        raise TimeoutError("fixture builder event timeout")

    def send(command):
        process.stdin.write(json.dumps(command) + "\n")
        process.stdin.flush()

    try:
        wait(lambda row: row.get("event") == "ready")
        latest = wait(lambda row: row.get("event") == "observation")
        for index, step in enumerate(PRELUDE):
            identifier = f"fixture-prelude-{index}"
            program = coast_steps(step["duration_ms"]) if step["kind"] == "coast" else compile_commands(step["commands"])
            send({"op": "submit", "id": identifier, "expected_sequence": latest["sequence"],
                  "valid_until_ns": time.perf_counter_ns() + 15_000_000_000, "steps": program})
            accepted = wait(lambda row: row.get("event") in ("accepted", "rejected") and
                            (row.get("id") == identifier or row.get("event") == "rejected"))
            if accepted["event"] != "accepted":
                raise RuntimeError(accepted)
            terminal = wait(lambda row: row.get("event") == "terminal" and row.get("id") == identifier)
            if terminal["status"] != "completed" or not terminal["release"]["verified"]:
                raise RuntimeError(terminal)
        send({"op": "save_fixture"})
        saved = wait(lambda row: row.get("event") == "fixture_saved")
        process.wait(timeout=20)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        (args.out / "stderr.txt").write_text(process.stderr.read())
    summary = {
        "schema": "map01_threat_fixture_build_report_v1", "passed": True,
        "fixture": saved["save"], "fixture_manifest": saved["manifest"],
        "fixture_sha256": saved["save_sha256"], "episode_tic": saved["episode_tic"],
        "source_sequence": saved["source_sequence"],
        "programs": len(PRELUDE),
        "verified_releases": sum(row.get("event") == "terminal" and
                                 row.get("release", {}).get("verified") for row in events),
        "model_calls": 0,
    }
    (args.out / "report.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
