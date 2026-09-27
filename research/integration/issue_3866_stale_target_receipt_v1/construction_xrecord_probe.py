#!/usr/bin/python3
"""Exercise only the observer on an empty Xvfb; no GUI task or workbook."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    display = ":98"
    env = dict(os.environ, DISPLAY=display, HOME="/tmp/xrec-home")
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "640x480x24",
                             "-nolisten", "tcp", "-ac"], env=env,
                            stdout=(out/"xvfb.log").open("w"),
                            stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic()+10
        while not Path("/tmp/.X11-unix/X98").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Xvfb did not start")
            time.sleep(0.05)
        events, ready, stop = out/"events.jsonl", out/"ready.json", out/"stop"
        monitor = subprocess.Popen([
            "/usr/bin/python3", "/src/record_monitor.py", "--display", display,
            "--events", str(events), "--ready", str(ready), "--stop", str(stop)],
            env=env, stdout=(out/"monitor.stdout").open("w"),
            stderr=(out/"monitor.stderr").open("w"))
        deadline = time.monotonic()+10
        while not ready.exists():
            if time.monotonic() > deadline:
                raise TimeoutError("XRecord did not report readiness")
            time.sleep(0.05)
        subprocess.run(["xdotool", "key", "Return"], env=env, check=True)
        time.sleep(0.2)
        stop.write_text("stop\n")
        monitor.wait(timeout=5)
        rows = [json.loads(x) for x in events.read_text().splitlines() if x]
        types = [x["type"] for x in rows]
        result = {"scope": "observer calibration only",
                  "event_count": len(rows), "event_types": types,
                  "monitor_exit": monitor.returncode,
                  "expected_types": [2, 3],
                  "pass": types == [2, 3] and monitor.returncode == 0}
        (out/"result.json").write_text(json.dumps(result, indent=2)+"\n")
        print(json.dumps(result, indent=2))
        if not result["pass"]:
            raise SystemExit(2)
    finally:
        xvfb.terminate()
        xvfb.wait(timeout=5)


if __name__ == "__main__":
    main()

