import json
import os
import sys
import argparse
import hashlib
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--effect", required=True)
parser.add_argument("--ready", required=True)
parser.add_argument("--done", required=True)
parser.add_argument("--limit", required=True, type=int)
args = parser.parse_args()
path = args.effect
limit = args.limit
sequence = 0
try:
    tty_name = os.ttyname(0)
except OSError as exc:
    tty_name = repr(exc)
Path(args.ready).write_text(json.dumps({"pid": os.getpid(), "stdin_tty": sys.stdin.isatty(), "stdin_name": tty_name}))
print(f"fixture-start pid={os.getpid()} path={path} limit={limit}", file=sys.stderr, flush=True)
for raw in sys.stdin:
    value = raw.rstrip("\r\n")
    print(f"fixture-input {value!r}", file=sys.stderr, flush=True)
    with open(path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"value": value}, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    sequence += 1
    if sequence >= limit:
        break
Path(args.done).write_text(json.dumps({"pid": os.getpid(), "actions": sequence, "exit": "normal"}, sort_keys=True))
print(f"fixture-exit sequence={sequence}", file=sys.stderr, flush=True)
