#!/usr/bin/env python3
"""Supplemental read-only audit of retained A02 isolated-control positions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def token_for(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def audit_rows(rows: list[dict], design: dict) -> dict:
    expected = {
        token_for(f"7387-t0|isolated|{cue}|{position}"): position
        for cue in design["cues"]
        for position in design["isolated_positions"]
    }
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        token = row.get("token")
        if token not in expected or token in seen:
            errors.append("isolated-key-or-duplicate")
            continue
        seen.add(token)
        position = row.get("position")
        if type(position) is not int or position != expected[token]:
            errors.append("isolated-position-mismatch")
    if len(rows) != len(expected):
        errors.append("isolated-denominator")
    if seen != set(expected):
        errors.append("isolated-coverage")
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "position_rows": len(seen),
        "expected_rows": len(expected),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--isolated", type=Path, required=True)
    args = parser.parse_args()
    design = json.loads(args.design.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in args.isolated.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(json.dumps(audit_rows(rows, design), sort_keys=True))


if __name__ == "__main__":
    main()
