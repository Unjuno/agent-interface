#!/usr/bin/env python3
"""Assemble the two isolated arm streams into the frozen auditor's JSONL."""
import hashlib
import json
from pathlib import Path
import sys


def load(path, policy):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if not rows or rows[0].get("type") != "freeze" or rows[0].get("policy") != policy:
        raise ValueError(f"{policy}: missing/mismatched freeze record")
    freeze = rows[0]
    schedule = json.dumps(freeze["events"], sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(schedule).hexdigest() != freeze["schedule_sha256"]:
        raise ValueError(f"{policy}: schedule digest mismatch")
    if freeze["events"] != __import__("run").EVENTS:
        raise ValueError(f"{policy}: event schedule differs from frozen source")
    if len([row for row in rows[1:] if row.get("type") == "state_snapshot"]) != 3:
        raise ValueError(f"{policy}: expected one full state snapshot per worker segment")
    if any(row.get("policy") != policy for row in rows[1:]):
        raise ValueError(f"{policy}: cross-arm record detected")
    return freeze, rows[1:]


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: assemble_container_raw.py CLEAR.jsonl TOMBSTONE.jsonl OUT.jsonl")
    clear_freeze, clear_rows = load(sys.argv[1], "clear")
    tomb_freeze, tomb_rows = load(sys.argv[2], "tombstone")
    if clear_freeze["events"] != tomb_freeze["events"]:
        raise ValueError("arm schedules differ")
    if clear_freeze["schedule_sha256"] != tomb_freeze["schedule_sha256"]:
        raise ValueError("arm schedule digests differ")
    records = [clear_freeze, *clear_rows, *tomb_rows]
    Path(sys.argv[3]).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    print(json.dumps({"records": len(records), "schedule_sha256": clear_freeze["schedule_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
