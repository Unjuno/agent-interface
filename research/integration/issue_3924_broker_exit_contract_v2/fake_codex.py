#!/usr/bin/env python3
"""Deterministic fake Codex child used by Issue #4485; never calls a model."""
import json
import os
from pathlib import Path
import sys
import time

record_root = Path(os.environ["FAKE_RECORD_ROOT"])
record_root.mkdir(parents=True, exist_ok=True)
seq = len(list(record_root.glob("invocation-*.json"))) + 1
record = {
    "argv": sys.argv[1:],
    "stdin": sys.stdin.read(),
    "pid": os.getpid(),
    "configured_exit": int(os.environ.get("FAKE_EXIT", "0")),
    "sleep_s": float(os.environ.get("FAKE_SLEEP_S", "0")),
    "stdout": os.environ.get("FAKE_STDOUT", '{"ok":true}'),
    "stderr": os.environ.get("FAKE_STDERR", ""),
}
path = record_root / f"invocation-{seq:02d}.json"
path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
time.sleep(record["sleep_s"])
sys.stdout.write(record["stdout"])
sys.stderr.write(record["stderr"])
raise SystemExit(record["configured_exit"])
