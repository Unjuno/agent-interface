#!/usr/bin/env python3
"""Deterministic fake Codex child; never calls a provider or real model."""
import json
import os
from pathlib import Path
import sys
import time

record = {
    "argv": sys.argv[1:],
    "stdin": sys.stdin.read(),
    "pid": os.getpid(),
    "configured_exit": int(os.environ.get("FAKE_EXIT", "0")),
    "sleep_s": float(os.environ.get("FAKE_SLEEP_S", "0")),
}
record_root = Path(os.environ["FAKE_RECORD_ROOT"])
record_root.mkdir(parents=True, exist_ok=True)
seq = len(list(record_root.glob("invocation-*.json"))) + 1
record["stdout"] = os.environ.get("FAKE_STDOUT", '{"ok":true}')
record["stderr"] = os.environ.get("FAKE_STDERR", "")
record_path = record_root / f"invocation-{seq:02d}.json"
record_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
time.sleep(record["sleep_s"])
sys.stdout.write(record["stdout"])
sys.stderr.write(record["stderr"])
raise SystemExit(record["configured_exit"])
