#!/usr/bin/env python3
"""Create the candidate's truth-blind read-only input bundle."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "formal" / "candidate_input"


def main():
    if DEST.exists():
        raise FileExistsError(f"refusing to replace frozen bundle: {DEST}")
    (DEST / "frames").mkdir(parents=True)
    shutil.copy2(ROOT / "candidate.py", DEST / "candidate.py")
    shutil.copy2(ROOT / "candidate_input.json", DEST / "candidate_input.json")
    rows = json.loads((DEST / "candidate_input.json").read_text())["rows"]
    for row in rows:
        for name in (row["frame0"], row["frame1"]):
            shutil.copy2(ROOT / name, DEST / name)
    files = sorted(p for p in DEST.rglob("*") if p.is_file())
    manifest = {str(p.relative_to(DEST)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in files}
    (ROOT / "CANDIDATE_INPUT_SHA256.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    forbidden = {"truth.json", "audit.py", "test_construction.py"}
    assert not forbidden.intersection(p.name for p in DEST.rglob("*"))
    assert len([p for p in files if p.suffix == ".pgm"]) == 72


if __name__ == "__main__":
    main()
