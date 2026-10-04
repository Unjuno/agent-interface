#!/usr/bin/env python3
"""Build the frozen PR #7682 + #7683 adapter candidate from Git blobs."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_PATH = (
    "research/integration/mindustry_three_arm_economics_20260928/"
    "target_socket_submit_v1.py"
)
RELEASE_HEAD = "1d7bb20bcde67333f58e41a24f8dce68f8561ffd"
STATUS_HEAD = "bd0ba260acf885d7b859d665571b2c3260666642"
NEEDLE = "        terminal = terminals[0]\n        release = terminal.get(\"release\")"
REPLACEMENT = (
    "        terminal = terminals[0]\n"
    "        if terminal.get(\"status\") != \"completed\":\n"
    "            raise SocketSubmitStop(\"matching terminal must report completed action\")\n"
    "        release = terminal.get(\"release\")"
)


def git_show(revision: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{SOURCE_PATH}"], cwd=HERE, stderr=subprocess.PIPE
    )


def main() -> None:
    release_source = git_show(RELEASE_HEAD)
    status_source = git_show(STATUS_HEAD).decode("utf-8")
    if REPLACEMENT not in status_source:
        raise SystemExit("pinned #7682 status guard is absent or changed")
    candidate = release_source.decode("utf-8")
    if candidate.count(NEEDLE) != 1:
        raise SystemExit("pinned #7683 candidate patch anchor is absent or ambiguous")
    candidate_bytes = candidate.replace(NEEDLE, REPLACEMENT, 1).encode("utf-8")
    output = HERE / "candidate_adapter.py"
    output.write_bytes(candidate_bytes)
    print(hashlib.sha256(candidate_bytes).hexdigest())


if __name__ == "__main__":
    main()
