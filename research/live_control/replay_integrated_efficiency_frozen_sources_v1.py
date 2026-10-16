"""Re-audit retained live-01 results using the exact preregistered sources.

This reconstructs a temporary source tree from the non-executable `.source`
archive, runs the checked-in post-run auditor against copied retained results,
and compares its output with the preserved historical audit. It never writes
to the retained study directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-01"
ARCHIVE = HERE / "results" / "integrated-efficiency-live-01-frozen-source-v1"
RESULT = HERE / "results" / "integrated-efficiency-live-01-frozen-source-audit-v1.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    plan = read(OUT / "preregistration.json")
    manifest = read(ARCHIVE / "SOURCE_MANIFEST.json")
    entries = {row["name"]: row for row in manifest["files"]}
    if set(entries) != set(plan["sources"]):
        raise SystemExit("frozen source archive does not match preregistration names")

    verified = {}
    with tempfile.TemporaryDirectory(prefix="integrated-efficiency-frozen-audit-") as temp:
        root = Path(temp) / "research" / "live_control"
        root.mkdir(parents=True)
        shutil.copytree(OUT, root / "results" / "integrated-efficiency-live-01")
        shutil.copy2(HERE / "audit_integrated_efficiency_live_v1.py",
                     root / "audit_integrated_efficiency_live_v1.py")
        for name, expected in plan["sources"].items():
            entry = entries[name]
            blob = (ARCHIVE / entry["archive_file"]).read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            if digest != expected or digest != entry["sha256"]:
                raise SystemExit(f"frozen source hash mismatch: {name}")
            (root / name).write_bytes(blob)
            verified[name] = digest

        completed = subprocess.run(
            ["python3", str(root / "audit_integrated_efficiency_live_v1.py")],
            cwd=root, text=True, capture_output=True, check=False)
        fresh = None
        if completed.returncode == 0:
            fresh = read(root / "results" / "integrated-efficiency-live-01" / "audit.json")
    prior = read(OUT / "audit.json")
    output = {
        "schema": "integrated_efficiency_live_frozen_source_audit_v1",
        "study": "integrated-efficiency-live-01",
        "source_commit": manifest["source_commit"],
        "source_count": len(verified),
        "all_preregistered_source_hashes_match": len(verified) == len(plan["sources"]),
        "audit_exit_code": completed.returncode,
        "audit_stdout": completed.stdout,
        "audit_stderr": completed.stderr,
        "fresh_audit_matches_preserved_audit": fresh == prior,
        "fresh_audit": fresh,
        "scope_note": "This replays the retained JSON audit with exact pinned source bytes. It does not rerun GUI/model execution or independently establish the original runtime checkout identity.",
    }
    print(json.dumps(output, indent=2))
    if args.write:
        RESULT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0 if completed.returncode == 0 and fresh == prior else 2


if __name__ == "__main__":
    raise SystemExit(main())
