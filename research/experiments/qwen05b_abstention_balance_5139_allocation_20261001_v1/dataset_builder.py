"""Allocation-specific wrapper over the current-main synthetic dataset builder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ALLOCATION = "QWEN-SUPPORT-BALANCE-5139-20261001-01"
SEEDS = {"formal_seed": 898659560, "support_seed": 582882955, "heldout_seed": 292197310}
SOURCE_DIR = Path(__file__).resolve().parents[1] / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(SOURCE_DIR))
from make_dataset import build as build_current_main  # noqa: E402


def build():
    doc = build_current_main(SEEDS["formal_seed"], SEEDS["support_seed"], SEEDS["heldout_seed"])
    doc["allocation"] = ALLOCATION
    return doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = (json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit("STOP_DATA_OUTPUT_EXISTS")
    path.write_bytes(payload)
    print(json.dumps({"allocation": ALLOCATION, "bytes": len(payload),
                      "sha256": __import__("hashlib").sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
