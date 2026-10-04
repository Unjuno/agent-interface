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
    allowed_keys = {"token", "position", "prompt", "source_indices", "frames"}
    expected = {
        token_for(f"7387-t0|isolated|{cue}|{position}"): position
        for cue in design["cues"]
        for position in design["isolated_positions"]
    }
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("isolated-schema-mismatch")
            continue
        if set(row) != allowed_keys:
            errors.append("isolated-schema-mismatch")
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


def audit_presentation_schema(rows: list[object], design: dict) -> dict:
    allowed_keys = {"token", "arm", "prompt", "source_indices", "frames"}
    expected_rows = (len(design["lags"]) * len(design["t2_positions"])
                     * len(design["ordered_pairs"]) * len(design["arms"]))
    errors = []
    if len(rows) != expected_rows:
        errors.append("presentation-denominator")
    if any(not isinstance(row, dict) or set(row) != allowed_keys for row in rows):
        errors.append("presentation-schema-mismatch")
    return {"ok": not errors, "errors": sorted(set(errors)),
            "presentation_rows": len(rows), "expected_rows": expected_rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--isolated", type=Path, required=True)
    parser.add_argument("--presentations", type=Path, required=True)
    args = parser.parse_args()
    design = json.loads(args.design.read_text(encoding="utf-8"))
    isolated_rows = [
        json.loads(line)
        for line in args.isolated.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    presentation_rows = [
        json.loads(line)
        for line in args.presentations.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    positions = audit_rows(isolated_rows, design)
    schema = audit_presentation_schema(presentation_rows, design)
    result = {"ok": positions["ok"] and schema["ok"],
              "position_audit": positions, "presentation_schema_audit": schema}
    print(json.dumps(result, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
