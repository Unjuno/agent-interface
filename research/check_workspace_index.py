#!/usr/bin/env python3
"""Check that every top-level research directory is reachable from the workspace indexes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE_README = ROOT / "README.md"
ROOT_MAP = ROOT / "ROOT_NAMESPACE_MAP.md"

LINK_RE = re.compile(r"\]\(([^)#]+?)/\)")


def top_level_dirs() -> set[str]:
    return {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }


def one_segment_links(text: str) -> set[str]:
    result: set[str] = set()
    for target in LINK_RE.findall(text):
        if target.startswith(".") or "/" in target:
            continue
        result.add(target)
    return result


def main() -> int:
    dirs = top_level_dirs()
    text = (
        WORKSPACE_README.read_text(encoding="utf-8")
        + "\n"
        + ROOT_MAP.read_text(encoding="utf-8")
    )
    linked = one_segment_links(text)

    missing = sorted(dirs - linked)
    dangling = sorted(linked - dirs)

    if missing or dangling:
        if missing:
            print("Top-level research directories missing from README/ROOT_NAMESPACE_MAP:")
            for name in missing:
                print(f"  - {name}")
        if dangling:
            print("Workspace indexes link to missing top-level research directories:")
            for name in dangling:
                print(f"  - {name}")
        return 1

    print(f"research workspace index OK: {len(dirs)} top-level directories reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
