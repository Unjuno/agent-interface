#!/usr/bin/env python3
"""Check that retained analytical results are indexed in research/analysis/README.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"

LINK_RE = re.compile(r"\[\x60([^\x60]+?)/\x60\]\(([^)]+)/\)")


def retained_result_dirs() -> set[str]:
    return {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and ((path / "REPORT.md").is_file() or (path / "FORMAL_FAILURE.md").is_file())
    }


def indexed_dirs(text: str) -> set[str]:
    result: set[str] = set()
    for label, target in LINK_RE.findall(text):
        if label == target:
            result.add(target)
    return result


def main() -> int:
    text = README.read_text(encoding="utf-8")
    retained = retained_result_dirs()
    indexed = indexed_dirs(text)

    missing = sorted(retained - indexed)
    dangling = sorted(indexed - {p.name for p in ROOT.iterdir() if p.is_dir()})

    if missing or dangling:
        if missing:
            print("Missing retained analytical results from README:")
            for name in missing:
                print(f"  - {name}")
        if dangling:
            print("README links to missing analytical directories:")
            for name in dangling:
                print(f"  - {name}")
        return 1

    print(f"analysis index OK: {len(retained)} retained result/failure directories indexed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
