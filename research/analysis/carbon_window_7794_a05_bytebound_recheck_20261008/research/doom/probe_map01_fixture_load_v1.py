"""Load a MAP01 fixture in a fresh v7 process and retain its first exact frame."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=990619)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    process = subprocess.Popen([
        sys.executable, str(HERE / "session_map01_v7.py"),
        "--out", str(args.out / "runtime"), "--seed", str(args.seed),
        "--load-fixture-manifest", str(args.fixture_manifest),
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
       text=True, bufsize=1)
    incoming = queue.Queue()

    def reader():
        for line in process.stdout:
            incoming.put(json.loads(line))

    threading.Thread(target=reader, daemon=True).start()

    def wait(predicate, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                row = incoming.get(timeout=min(.25, deadline - time.monotonic()))
            except queue.Empty:
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read())
                continue
            if predicate(row):
                return row
        raise TimeoutError("fixture load event timeout")

    try:
        ready = wait(lambda row: row.get("event") == "ready")
        initial = wait(lambda row: row.get("event") == "observation")
        process.stdin.write('{"op":"finish"}\n')
        process.stdin.flush()
        score = wait(lambda row: row.get("event") == "post_control_score")
        process.wait(timeout=20)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        (args.out / "stderr.txt").write_text(process.stderr.read())
    image = Path(initial["image"])
    report = {
        "schema": "map01_fixture_load_probe_v1", "passed": True,
        "fixture": ready["fixture"], "initial_observation": initial,
        "initial_image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "score": score, "model_calls": 0,
        "scope": "fresh-process load and X11 observation only; no control-performance claim",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "passed": True, "initial_image": initial["image"],
        "initial_sequence": initial["sequence"],
        "source_episode_tic": ready["fixture"]["source_episode_tic"],
        "after_load_tic": ready["fixture"]["after_load_tic"],
        "player_dead": score["player_dead"], "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
