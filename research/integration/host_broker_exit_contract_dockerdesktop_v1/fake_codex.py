#!/usr/local/bin/python3
import json
import os
import sys
import time
from pathlib import Path

capture = {"argv": sys.argv[1:], "stdin": sys.stdin.read(),
           "configured_exit": int(os.environ.get("FAKE_EXIT", "0")),
           "configured_sleep_s": float(os.environ.get("FAKE_SLEEP_S", "0"))}
Path(os.environ["FAKE_CAPTURE_PATH"]).write_text(json.dumps(capture, sort_keys=True) + "\n")
if capture["configured_sleep_s"]:
    time.sleep(capture["configured_sleep_s"])
sys.stdout.write(os.environ.get("FAKE_STDOUT", '{"fake":true}\n'))
sys.stderr.write(os.environ.get("FAKE_STDERR", "fake-stderr\n"))
raise SystemExit(capture["configured_exit"])
