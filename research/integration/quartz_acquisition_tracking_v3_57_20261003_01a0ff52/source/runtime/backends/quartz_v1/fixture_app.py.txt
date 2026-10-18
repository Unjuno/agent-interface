"""Independent macOS dialog fixture for Quartz backend effect scoring."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

if sys.platform != "darwin":
    raise SystemExit("fixture requires macOS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    args = parser.parse_args()
    args.meta.parent.mkdir(parents=True, exist_ok=True)
    script = 'display dialog "Agent Interface Quartz fixture" default answer "" buttons {"OK"} default button "OK" with title "Agent Interface Quartz Fixture"'
    proc = subprocess.Popen(["/usr/bin/osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(0.5)
    if proc.poll() is not None:
        out, err = proc.communicate()
        raise RuntimeError(f"osascript exited early rc={proc.returncode} stdout={out!r} stderr={err!r}")
    args.meta.write_text(json.dumps({"pid": proc.pid}, sort_keys=True), encoding="utf-8")
    with args.events.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": "ready", "pid": proc.pid}) + "\n")
    out, err = proc.communicate()
    with args.events.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": "terminal", "rc": proc.returncode, "stdout": out, "stderr": err}, sort_keys=True) + "\n")
    if proc.returncode != 0:
        return proc.returncode
    text = ""
    if "text returned:" in out:
        text = out.split("text returned:", 1)[1].strip()
        if "," in text:
            text = text.split(",", 1)[0].strip()
    result = {"accepted": True, "text": text, "stdout": out.strip()}
    args.effect.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
