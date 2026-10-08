#!/usr/bin/env python3
"""Synthetic, no-model PTY probe for one 13,449-byte framed event."""
import json
import sys
from row_frames import decode_call, encode_call

prefix = b'{"payload":"'
suffix = b'"}'
payload = prefix + b"x" * (13_449 - len(prefix) - len(suffix)) + suffix
if len(payload) != 13_449:
    raise SystemExit("wrong synthetic payload size")
frames = encode_call(1, payload)
if decode_call(frames, 1) != payload:
    raise SystemExit("local frame round trip failed")
for frame in frames:
    sys.stdout.write(frame + "\n")
    sys.stdout.flush()
ack = sys.stdin.readline().strip()
if ack != "ACK 1":
    raise SystemExit("STOP: exact readback ACK missing")
print("PROBE_ACKED", flush=True)
