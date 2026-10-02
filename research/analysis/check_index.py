#!/usr/bin/env python3
"""Check or refresh the generated retained-result index in research/analysis/README.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"

HEADING = "## Complete retained result directory index"
BEGIN = "<!-- BEGIN GENERATED ANALYSIS RESULT INDEX -->"
END = "<!-- END GENERATED ANALYSIS RESULT INDEX -->"
LINK_RE = re.compile(r"\[\x60([^\x60]+?)/\x60\]\(([^)]+)/\)")


def retained_result_dirs() -> list[str]:
    return sorted(
        path.name
        for path in ROOT.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and (
            (path / "REPORT.md").is_file()
            or (path / "FORMAL_FAILURE.md").is_file()
            or (path / "STOP.md").is_file()
        )
    )


def checkout_is_sparse() -> bool:
    """True when Git's sparse-checkout metadata is available and enabled."""
    checkout = ROOT.parents[2]
    git_file = checkout / ".git"
    if git_file.is_file():
        content = git_file.read_text(encoding="utf-8").strip()
        if not content.startswith("gitdir:"):
            return False
        git_dir = (checkout / content.split(":", 1)[1].strip()).resolve()
    elif git_file.is_dir():
        git_dir = git_file
    else:
        return False
    return (git_dir / "info" / "sparse-checkout").is_file()


def render_block(names: list[str]) -> str:
    lines = [
        HEADING,
        "",
        "This compact list is generated from child directories that contain `REPORT.md` or "
        "`FORMAL_FAILURE.md`, or `STOP.md`. It is the completeness surface used by the index checker.",
        "",
        BEGIN,
        "",
        "<details>",
        "<summary><strong>Expand all retained result/failure directories</strong></summary>",
        "",
    ]
    lines.extend(f"- [`{name}/`]({name}/)" for name in names)
    lines.extend(["", "</details>", "", END])
    return "\n".join(lines)


def generated_entries(text: str) -> list[str]:
    if BEGIN not in text or END not in text:
        return []
    body = text.split(BEGIN, 1)[1].split(END, 1)[0]
    return [
        target
        for label, target in LINK_RE.findall(body)
        if label.rstrip("/") == target.rstrip("/")
    ]


def generated_dirs(text: str) -> set[str]:
    return set(generated_entries(text))


def with_generated_block(text: str, block: str) -> str:
    if HEADING in text and END in text:
        start = text.index(HEADING)
        stop = text.index(END, start) + len(END)
        return text[:start] + block + text[stop:]

    marker = "\n## Interpretation\n"
    if marker not in text:
        raise RuntimeError("README has no generated-index block and no Interpretation insertion point")
    return text.replace(marker, "\n" + block + "\n" + marker, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite the generated retained-result/failure/STOP directory block in README.md",
    )
    args = parser.parse_args()

    names = retained_result_dirs()
    sparse = checkout_is_sparse()
    current = README.read_text(encoding="utf-8")
    expected = with_generated_block(current, render_block(names))

    if args.write:
        if expected != current:
            README.write_text(expected, encoding="utf-8")
            print(f"analysis index refreshed: {len(names)} retained result/failure directories")
        else:
            print(f"analysis index already current: {len(names)} retained result/failure directories")
        return 0

    if expected != current:
        retained = set(names)
        entries = generated_entries(current)
        indexed = generated_dirs(current)
        existing = {path.name for path in ROOT.iterdir() if path.is_dir()}
        missing = sorted(retained - indexed)
        stale = sorted(indexed - retained)
        dangling = sorted(indexed - existing)

        if entries != sorted(entries) or len(entries) != len(indexed):
            print("Generated analytical result/failure/STOP index is duplicated or unsorted.")
            return 1

        print("Generated analytical result/failure/STOP index is stale.")
        if missing:
            print("Missing retained result/failure directories:")
            for name in missing:
                print(f"  - {name}")
        if stale and not sparse:
            print("Generated entries no longer qualify as retained results/failures/STOPs:")
            for name in stale:
                print(f"  - {name}")
        if dangling and not sparse:
            print("Generated entries point to missing directories:")
            for name in dangling:
                print(f"  - {name}")
        if missing or (stale or dangling) and not sparse:
            print("Run: python research/analysis/check_index.py --write")
            return 1
        if stale or dangling:
            print("Sparse checkout: absent sibling directories were not treated as removals.")
        return 0

    print(f"analysis index OK: {len(names)} retained result/failure directories indexed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
