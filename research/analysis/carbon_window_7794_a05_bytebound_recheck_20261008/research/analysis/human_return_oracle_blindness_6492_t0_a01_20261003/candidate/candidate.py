#!/usr/bin/env python3
"""Build non-authoritative return packets from public observations only."""

import argparse
import json
from pathlib import Path


SCHEMA = "human-return-oracle-blindness-candidate-v1"


def packet_for(row):
    if not isinstance(row, dict):
        raise ValueError("each public row must be an object")

    release_required = row.get("emergency_release_required") is True
    packet = {
        "status": "UNKNOWN",
        "cue": None,
        "target": None,
        "authority": "NONE",
        "release_required": release_required,
    }

    view = row.get("view")
    if not isinstance(view, dict):
        return packet
    if row.get("window_matches_task") is not True:
        return packet
    if row.get("view_epoch") != row.get("current_epoch"):
        return packet

    cue = row.get("cue")
    if not isinstance(cue, dict):
        return packet
    if cue.get("origin") != "USER":
        return packet
    if cue.get("epoch") != row.get("current_epoch"):
        return packet

    cue_text = cue.get("text")
    if not isinstance(cue_text, str) or not cue_text.strip():
        return packet

    packet["status"] = "CUE_AVAILABLE"
    packet["cue"] = cue_text
    return packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(source, dict) or not isinstance(source.get("rows"), list):
        raise ValueError("input must contain a rows array")

    result = {
        "schema": SCHEMA,
        "packets": [packet_for(row) for row in source["rows"]],
    }
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
