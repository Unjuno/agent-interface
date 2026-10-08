"""One-shot CPU-only fresh dataset construction; no model or runtime imports."""
from __future__ import annotations

import hashlib
import json
import platform
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
SOURCE = PACKAGE.parent / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(SOURCE))

from make_dataset import build  # noqa: E402

ALLOCATION = "QWEN-SUPPORT-BALANCE-5139-20261001-03-CPU-CONSTRUCTION"
SEEDS = (914728361, 672904183, 385167429)
OUTPUT = PACKAGE / "formal-dataset.json"


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    receipt_path = PACKAGE / "CANDIDATE.json"
    if receipt_path.exists():
        raise SystemExit("STOP_RECEIPT_ALREADY_EXISTS")
    started = datetime.now(timezone.utc).isoformat()
    document = build(*SEEDS)
    document["allocation"] = ALLOCATION
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with OUTPUT.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    summary = {
        "allocation": ALLOCATION,
        "bytes": len(payload),
        "candidate_exit_code": 0,
        "classes": len(document["classes"]),
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "formal_seed": SEEDS[0],
        "heldout_pool_rows": len(document["heldout_pool"]),
        "heldout_rows": len(document["heldout"]),
        "python": sys.version,
        "platform": platform.platform(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "started_utc": started,
        "support_pool_rows": len(document["support_pool"]),
        "support_seed": SEEDS[1],
        "support_rows": {arm: len(rows) for arm, rows in document["supports"].items()},
        "heldout_seed": SEEDS[2],
    }
    receipt_bytes = (json.dumps(summary, sort_keys=True) + "\n").encode("utf-8")
    with receipt_path.open("xb") as stream:
        stream.write(receipt_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    print(receipt_bytes.decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
