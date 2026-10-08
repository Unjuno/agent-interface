#!/usr/bin/env python3
"""Create a truth-bearing auditor bundle after candidate output is frozen."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "formal" / "audit_input"


def main():
    candidate_raw = ROOT / "formal" / "candidate_output" / "candidate.json"
    if not candidate_raw.is_file():
        raise FileNotFoundError("formal candidate output is absent")
    if DEST.exists():
        raise FileExistsError(f"refusing to replace frozen auditor input: {DEST}")
    (DEST / "frames").mkdir(parents=True)
    for name in ("audit.py", "truth.json", "candidate_input.json"):
        shutil.copy2(ROOT / name, DEST / name)
    shutil.copy2(candidate_raw, DEST / "candidate.json")
    rows = json.loads((DEST / "truth.json").read_text())["rows"]
    for row in rows:
        for name in (row["frame0"], row["frame1"]):
            shutil.copy2(ROOT / name, DEST / name)
    manifest = {str(p.relative_to(DEST)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(DEST.rglob("*")) if p.is_file()}
    (ROOT / "AUDIT_INPUT_SHA256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assert not (DEST / "candidate.py").exists()
    assert len([p for p in DEST.rglob("*.pgm")]) == 72


if __name__ == "__main__":
    main()
