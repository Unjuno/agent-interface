#!/usr/bin/env python3
"""Redact Codex installation/quota metadata from a public protocol log.

Model requests, replies, turn identifiers, model usage, and ordering are retained.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def redact(data: bytes) -> bytes:
    output = []
    for line in data.splitlines():
        if not line:
            continue
        row = json.loads(line)
        message = row.get("message", {})
        method = message.get("method")
        params = message.get("params")
        changed = False
        if method == "remoteControl/status/changed" and isinstance(params, dict):
            for key in ("installationId", "serverName", "environmentId"):
                changed |= params.pop(key, None) is not None
        elif method == "account/updated" and isinstance(params, dict):
            changed |= params.pop("planType", None) is not None
        elif method == "account/rateLimits/updated" and isinstance(params, dict):
            message["params"] = {"redacted": "account-specific rate limits"}
            changed = True
        output.append((json.dumps(row, separators=(",", ":"), ensure_ascii=False)
                       if changed else line.decode("utf-8")))
    return ("\n".join(output) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.write_bytes(redact(args.source.read_bytes()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
