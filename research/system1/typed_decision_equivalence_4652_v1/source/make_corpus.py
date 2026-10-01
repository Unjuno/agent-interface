#!/usr/bin/env python3
"""Build the frozen synthetic cache-mechanics input; no task labels are emitted."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).with_name("corpus.jsonl")


def build() -> list[dict[str, object]]:
    rows = []
    for i in range(64):
        state = {
            "intent": f"bounded workflow case {i:02d}",
            "surface": f"surface-{i % 8}",
            "generation": 1000 + i,
            "evidence": [f"obs-{i:02d}-{j}" for j in range(3)],
            "candidates": [
                {"code": str(j), "kind": ("click", "type", "scroll", "wait")[j % 4],
                 "target": f"target-{(i + j) % 11}", "current": (i + j) % 5 != 0}
                for j in range(8)
            ],
        }
        prefix = (
            "<|im_start|>system\n"
            "You are a constrained operation/target readout. Never invent an operation, "
            "target, payload, or authority. Select only one listed code. The code is a "
            "mechanics probe and is not an authorization.\n"
            "<|im_end|>\n<|im_start|>user\n"
            "Current intent and candidates (synthetic fixture):\n"
            + json.dumps(state, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        questions = [
            f"Question slot {q:02d}: choose the listed code most compatible with the "
            f"current intent and evidence. Valid answer codes: 0 1 2 3 4 5 6 7.\n"
            "Return one code only.\n<|im_end|>\n<|im_start|>assistant\n"
            for q in range(16)
        ]
        rows.append({"bundle_id": f"B{i:02d}", "prefix": prefix, "suffixes": questions})
    return rows


def main() -> None:
    rows = build()
    data = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    OUT.write_text(data, encoding="utf-8", newline="\n")
    print(json.dumps({"path": OUT.name, "bundles": len(rows), "sha256": hashlib.sha256(data.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
