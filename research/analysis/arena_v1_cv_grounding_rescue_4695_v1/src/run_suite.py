#!/usr/bin/env python3
"""Run the frozen local proposal-only detector; this program sends no input."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from refine import detect

SOURCE_POINTS = {"case-01-retained-arena": [920, 640]}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_suite.py dataset-dir output.json")
    root, output = Path(sys.argv[1]), Path(sys.argv[2])
    rows = []
    for frame in sorted((root / "panels").glob("*.png")):
        row = {"id": frame.stem, **detect(frame)}
        if frame.stem in SOURCE_POINTS:
            row["source_point_xy"] = SOURCE_POINTS[frame.stem]
        rows.append(row)
    output.write_text(json.dumps({"rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "proposals": sum(r["status"] == "PROPOSAL" for r in rows), "abstentions": sum(r["status"] == "ABSTAIN" for r in rows)}, indent=2))


if __name__ == "__main__":
    main()
