#!/usr/bin/env python3
"""Corrected third synthetic PTY probe; no model calls."""
import json
import sys
from row_frames import decode_call, encode_call

prefix = b'{"payload":"'
suffix = b'"}'
payload = prefix + b"z" * (13_449 - len(prefix) - len(suffix)) + suffix
assert len(payload) == 13_449
assert len(json.loads(payload)["payload"]) == len(payload) - len(prefix) - len(suffix)
frames = encode_call(1, payload)
assert decode_call(frames, 1) == payload
for frame in frames:
    sys.stdout.write(frame + "\n")
    sys.stdout.flush()
if sys.stdin.readline().strip() != "ACK 1":
    raise SystemExit("STOP: ACK missing")
print("PROBE_ACKED", flush=True)
