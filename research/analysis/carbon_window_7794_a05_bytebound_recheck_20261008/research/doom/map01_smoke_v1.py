"""No-input feasibility smoke for the normal Freedoom MAP01 adapter."""

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.out / "runtime"
    process = subprocess.Popen([
        sys.executable, str(HERE / "session_map01_v1.py"), "--out", str(runtime),
        "--seed", "990601", "--timeout-seconds", "600"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1)
    received = queue.Queue()
    threading.Thread(target=lambda: [received.put(json.loads(line))
                                      for line in process.stdout], daemon=True).start()
    events = []

    def wait(kind):
        while True:
            row = received.get(timeout=30)
            events.append(row)
            if row["event"] == kind:
                return row

    clock = wait("clock_probe")
    ready = wait("ready")
    initial = wait("observation")
    process.stdin.write(json.dumps({"op": "finish"}) + "\n")
    process.stdin.flush()
    score = wait("post_control_score")
    process.wait(timeout=20)
    (args.out / "stderr.txt").write_text(process.stderr.read())
    rate = (clock["after_tic"] - clock["before_tic"]) / clock["wall_seconds"]
    report = {"passed": process.returncode == 0 and 30 <= rate <= 40
              and ready["task"] == "Exit continuously advancing Freedoom MAP01"
              and score["map_exit"] is False and score["player_dead"] is False,
              "observed_tics_per_second": rate, "initial_observation": initial,
              "score": score, "input_programs": 0,
              "claim": "normal-map no-input feasibility only; not a clear attempt"}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("passed", "observed_tics_per_second", "input_programs", "claim")},
                     indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
