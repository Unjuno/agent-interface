#!/usr/bin/env python3
"""Validate repository-relative links in public navigation Markdown files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_DOCS = [
    "README.md",
    "RESEARCH.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/README.md",
    "docs/EVIDENCE_MAP.md",
    "docs/RESEARCH_METHOD.md",
    "docs/TERMINOLOGY.md",
    "docs/PROGRESS_FROM_BASELINE.md",
    "docs/principles.md",
    "docs/architecture.md",
    "docs/design-theses.md",
    "docs/control-codec.md",
    "docs/product-hunt.md",
    "research/README.md",
    "research/ROOT_NAMESPACE_MAP.md",
    "research/analysis/README.md",
    "research/concurrency/README.md",
    "research/system1/README.md",
    "research/local_system1/README.md",
    "runtime/README.md",
    "release/README.md",
    "site/README.md",
    ".github/README.md",
    ".github/workflows/README.md",
]

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def tracked_paths() -> set[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return {item.decode("utf-8") for item in raw.split(b"\0") if item}


def target_is_tracked(target: str, tracked: set[str]) -> bool:
    if target in tracked:
        return True
    prefix = target.rstrip("/") + "/"
    return any(path.startswith(prefix) for path in tracked)


def extract_target(raw: str) -> str | None:
    target = raw.strip()
    if not target:
        return None

    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        # Markdown permits an optional title after the destination.
        target = target.split(maxsplit=1)[0]

    if target.startswith("#") or target.startswith("//"):
        return None

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None

    path = unquote(parsed.path)
    if not path or path.startswith("/"):
        return None
    return path


def main() -> int:
    errors: list[str] = []
    checked_links = 0
    tracked = tracked_paths()

    for relative_doc in PUBLIC_DOCS:
        doc = ROOT / relative_doc
        if not doc.is_file():
            errors.append(f"missing public document: {relative_doc}")
            continue

        text = doc.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = extract_target(match.group(1))
            if target is None:
                continue

            checked_links += 1
            resolved = (doc.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{relative_doc}: link escapes repository: {target}")
                continue

            relative_target = resolved.relative_to(ROOT).as_posix()
            if not target_is_tracked(relative_target, tracked):
                errors.append(
                    f"{relative_doc}: missing tracked relative target: {target}"
                )

    if errors:
        print("Public navigation check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"public navigation OK: {len(PUBLIC_DOCS)} documents, "
        f"{checked_links} repository-relative links"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
