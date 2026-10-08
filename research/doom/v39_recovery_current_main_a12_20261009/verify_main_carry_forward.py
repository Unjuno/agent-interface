"""Verify the frozen regression source closure is byte-identical at current main."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
CURRENT_MAIN = "57337e95ecbecf7e762c8ec8091472b79e8ad49f"
OUTPUT = ROOT / "MAIN_CARRY_FORWARD.json"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), *args])


changed = git("diff", "--name-only", FREEZE["source_commit"], CURRENT_MAIN).decode().splitlines()
changed_set = set(changed)
source_rows = []
overlap = sorted(changed_set & set(RESULT["sources"]))
for path, expected in sorted(RESULT["sources"].items()):
    blob = git("rev-parse", f"{CURRENT_MAIN}:{path}").decode().strip()
    data = git("cat-file", "blob", blob)
    assert blob == expected["blob"], path
    assert hashlib.sha256(data).hexdigest() == expected["sha256"], path
    source_rows.append({"path": path, "blob": blob, "sha256": expected["sha256"]})

assert not overlap
record = {
    "frozen_source_commit": FREEZE["source_commit"],
    "current_main_commit": CURRENT_MAIN,
    "changed_paths_since_frozen_source": len(changed),
    "source_paths_verified": len(source_rows),
    "changed_paths_overlapping_pinned_sources": overlap,
    "sources": source_rows,
    "status": "PASS_BYTE_IDENTICAL_CURRENT_MAIN_CARRY_FORWARD",
    "scope": "Source applicability check only; the four suites were not rerun at current_main_commit.",
}
with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({key: record[key] for key in (
    "frozen_source_commit", "current_main_commit", "changed_paths_since_frozen_source",
    "source_paths_verified", "changed_paths_overlapping_pinned_sources", "status")}, indent=2))
