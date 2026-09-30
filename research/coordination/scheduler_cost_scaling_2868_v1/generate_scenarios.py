#!/usr/bin/env python3
"""Generate the immutable paired queue schedules for Issue #5021."""
import hashlib
import json
import sys
from pathlib import Path


SEED = "scheduler-cost-scaling-2868-v1-20260928-01"
SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15


def digest_int(*parts):
    value = ":".join(map(str, parts)).encode("ascii")
    return int(hashlib.sha256(value).hexdigest()[:16], 16)


def build_schedule():
    cases = []
    for size in SIZES:
        blocks = []
        for block in range(BLOCKS):
            candidates = []
            for seq in range(size):
                priority = digest_int(SEED, size, block, seq, "priority") % 7
                deadline = 10_000 + digest_int(SEED, size, block, seq, "deadline") % 19
                candidates.append([
                    -int(priority), int(deadline), seq,
                    "op-%04d" % seq,
                ])
            blocks.append({"block": block, "candidates": candidates})
        cases.append({"size": size, "blocks": blocks})
    return {
        "schema": "scheduler-cost-schedule-v1",
        "issue": 5021,
        "allocation": SEED,
        "seed": SEED,
        "ordering_key": ["negative_priority", "deadline", "enqueue_seq", "op_id"],
        "sizes": list(SIZES),
        "blocks_per_size": BLOCKS,
        "cases": cases,
    }


def main():
    target = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).with_name("scenarios.json")
    data = (json.dumps(build_schedule(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(json.dumps({"path": str(target), "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
