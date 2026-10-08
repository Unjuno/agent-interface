#!/usr/bin/env python3
"""Corrected second synthetic PTY probe; no model calls."""
import json
import sys
from row_frames import decode_call, encode_call

prefix = b'{"payload":"'
suffix = b'"}'
payload = prefix + b"y" * (13_449 - len(prefix) - len(suffix)) + suffix
if len(payload) != 13_449 or len(json.loads(payload)["payload"]) != 13_449 - len(prefix) - len(suffix):
    raise SystemExit("synthetic payload construction failed")
frames = encode_call(1, payload)
if decode_call(frames, 1) != payload:
    raise SystemExit("sender-side frame validation failed")
for frame in frames:
    sys.stdout.write(frame + "\n")
    sys.stdout.flush()
ack = sys.stdin.readline().strip()
if ack != "ACK 1":
    raise SystemExit("STOP: exact readback ACK missing")
print("PROBE_ACKED", flush=True)
