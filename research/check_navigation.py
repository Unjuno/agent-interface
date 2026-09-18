#!/usr/bin/env python3
"""Check that top-level research directories are covered by repository navigation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX_FILES = (ROOT / "README.md", ROOT / "ROOT_NAMESPACE_MAP.md")

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def top_level_links(text: str) -> set[str]:
    result: set[str] = set()
    for target in LINK_RE.findall(text):
        target = target.split("#", 1)[0]
        if not target or target.startswith("../") or "://" in target:
            continue
        target = target.rstrip("/")
        if "/" not in target and target not in {".", ".."}:
            result.add(target)
    return result


def main() -> int:
    actual = {
        p.name
        for p in ROOT.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }

    indexed: set[str] = set()
    for path in INDEX_FILES:
        indexed.update(top_level_links(path.read_text(encoding="utf-8")))

    missing = sorted(actual - indexed)
    dangling = sorted(indexed - actual)

    if missing or dangling:
        if missing:
            print("Unindexed top-level research directories:")
            for name in missing:
                print(f"  - {name}")
        if dangling:
            print("Navigation points to missing top-level research directories:")
            for name in dangling:
                print(f"  - {name}")
        return 1

    print(f"research navigation OK: {len(actual)} top-level directories covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
