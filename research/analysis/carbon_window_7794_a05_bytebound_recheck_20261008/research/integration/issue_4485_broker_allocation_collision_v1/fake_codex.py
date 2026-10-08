#!/usr/local/bin/python
import json
import os
import sys
import time

log = os.environ["FAKE_INVOCATIONS"]
with open(log, "a", encoding="utf-8") as stream:
    stream.write(json.dumps({"argv": sys.argv[1:], "prompt": sys.stdin.read()}) + "\n")
if os.environ.get("FAKE_MODE") == "sleep":
    time.sleep(2)
print('{"fake":true}')
raise SystemExit(int(os.environ.get("FAKE_EXIT", "0")))
