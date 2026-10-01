"""Verify a narrow historical source closure and preserve current frozen evidence.

Identity only: the immutable historical audit and current adapter regressions
run separately. This checker never dispatches or invokes the 800-row runner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HISTORICAL_COMMIT = "8588ae768b9d83e77d5a797fd2c7cfb588747cde"
STUDY = "research/integration/golden_v3_adapter_p2_rebase_2360_v1"
PINNED = {
    "runtime/cli_v1/golden_v3.py": "b72fa2203c9b8be7a03e084cee1e43c239efe92a",
    "runtime/cli_v1/__init__.py": "3156f21960bdc6470aea310179e7152b8100c686",
    "runtime/selector_v1/__init__.py": "1a09fab9f2f67777decfe2373b0108f3a2609678",
    "runtime/cli_v1/api.py": "f9dc26441c5f4ff9d7f57aa6a6a7b3849a1537d7",
    "runtime/selector_v1/selector.py": "bd85e9936258f4a13f2cd2455eb4a8350f1b9843",
    "research/integration/golden_v3_adapter_p2_rebase_2360_v1/test_adapter.py": "8e7d15eeb704c72f791b192a3489539554edd490",
    "research/integration/golden_v3_adapter_p2_rebase_2360_v1/SOURCE_MANIFEST.json": "5f3ec7d1b515db259f65bdca891e9a98c714398c",
    "research/integration/golden_v3_adapter_p2_rebase_2360_v1/audit.py": "30a0d10aa3a998f6ee18cebcbbf916e2f1038816",
    "research/integration/golden_v3_adapter_p2_rebase_2360_v1/README.md": "fc5b364fbcd2b11a5cbbf4c1fa11c9498e946cbc"
}
FROZEN = tuple(path for path in PINNED if path.startswith(STUDY + "/"))


def read_regular(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.is_file() or path.is_symlink() or path.resolve() != root / relative:
        raise ValueError("SOURCE_NOT_REGULAR: " + relative)
    if path.stat().st_size > 131072:
        raise ValueError("SOURCE_SIZE_LIMIT: " + relative)
    return path.read_bytes()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def verify(current: Path, historical: Path) -> dict:
    current, historical = current.resolve(), historical.resolve()
    if current == historical:
        raise ValueError("ROOTS_MUST_DIFFER")
    for relative, expected in PINNED.items():
        data = read_regular(historical, relative)
        if git_blob(data) != expected:
            raise ValueError("HISTORICAL_BLOB_CHANGED: " + relative)
    for relative in FROZEN:
        if read_regular(current, relative) != read_regular(historical, relative):
            raise ValueError("CURRENT_FROZEN_CHANGED: " + relative)
    # The closure contains real package initializers/API/selector dependencies.
    # Extra Python source could alter package imports in the historical lane.
    expected_python = {name for name in PINNED if name.endswith(".py")}
    actual_python = {
        path.relative_to(historical).as_posix()
        for folder in ("runtime", "research")
        for path in (historical / folder).rglob("*.py")
    }
    if actual_python != expected_python:
        raise ValueError("UNEXPECTED_HISTORICAL_SOURCE")
    return {
        "scope": "source_identity_only",
        "historical_commit": HISTORICAL_COMMIT,
        "historical_files_verified": len(PINNED),
        "current_frozen_files_preserved": len(FROZEN),
        "current_adapter_semantics": "not_checked_by_this_command",
        "formal_runner_invocations": 0,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-root", type=Path, default=root)
    parser.add_argument("--historical-root", type=Path, default=root / ".golden-p2-history")
    args = parser.parse_args()
    print(json.dumps(verify(args.current_root, args.historical_root), sort_keys=True))


if __name__ == "__main__":
    main()
