"""Verify the retained synthetic owner-receipt join packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest["entries"]
    mismatches = []
    for relative, expected in entries.items():
        path = (HERE / relative).resolve(strict=True)
        if not path.is_relative_to(HERE.resolve()):
            mismatches.append(f"path escapes packet: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(f"digest mismatch: {relative}")
    summary = json.loads((HERE / "matched_summary.json").read_text(encoding="utf-8"))
    conditions = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
    if set(summary["arms"]) != {"A", "B", "C"}:
        mismatches.append("matched block arm set is invalid")
    if conditions["provider_calls"] != 0 or conditions["gui_or_os_input"] != 0:
        mismatches.append("conditions do not describe a no-live-input synthetic run")
    print(json.dumps({
        "status": "PASS" if not mismatches else "FAIL",
        "manifest_entries": len(entries),
        "verified_entries": len(entries) - len(mismatches),
        "mismatches": mismatches,
    }, sort_keys=True))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
