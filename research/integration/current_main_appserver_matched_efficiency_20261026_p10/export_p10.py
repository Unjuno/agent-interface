"""Create a redacted public export without editing private raw outcomes."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from research.integration.current_main_appserver_matched_efficiency_20261026_p10.privacy_redact import redact_run

ROOT = Path(__file__).resolve().parent
CELLS = tuple(f"{pair}-{arm}" for pair, arms in (
    ("p01", ("direct_public_input", "compiled_public_caller")),
    ("p02", ("compiled_public_caller", "direct_public_input")),
    ("p03", ("direct_public_input", "compiled_public_caller"))) for arm in arms)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def export(raw_root):
    raw_root = Path(raw_root).resolve()
    audit_path = ROOT / "AUDIT-PRIVATE-VALIDATION.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("integrity_pass") is not True or audit.get("counts", {}).get("trial_cells") != 6:
        raise RuntimeError("private raw audit must validate all six first outcomes before export")
    public_root = ROOT / "run"
    if public_root.exists():
        raise FileExistsError(f"public export already exists: {public_root}")
    public_root.mkdir()
    for cell in CELLS:
        src = raw_root / cell
        manifest_path = src / "RAW-SHA256.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        audited_cell = audit.get("cells", {}).get(cell, {})
        if sha(manifest_path.read_bytes()) != audited_cell.get("private_raw_manifest_sha256"):
            raise ValueError(f"export raw manifest differs from private audit in {cell}")
        listed = {row["path"]: row for row in manifest["files"]}
        actual = {path.relative_to(src).as_posix(): path for path in src.rglob("*")
                  if path.is_file() and path.name != "RAW-SHA256.json"}
        if set(listed) != set(actual) or any(
                sha(actual[name].read_bytes()) != listed[name]["sha256"] or
                actual[name].stat().st_size != listed[name]["bytes"] for name in listed):
            raise ValueError(f"private raw manifest mismatch in {cell}")
        dst = public_root / cell
        dst.mkdir()
        shutil.copyfile(manifest_path, dst / "PRIVATE-RAW-SHA256.json")
        omitted = []
        for rel, path in actual.items():
            parts = Path(rel).parts
            if (path.suffix.lower() == ".bin" or
                    ("ledger" in parts and "raw" in parts)):
                omitted.append({"path": rel, "bytes": listed[rel]["bytes"],
                                "sha256": listed[rel]["sha256"]})
                continue
            target = dst / Path(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        report = redact_run(dst)
        export_manifest = {
            "schema": "agent-interface/p10-public-export-v1",
            "private_manifest_sha256": sha(manifest_path.read_bytes()),
            "omitted_private_raw_files": omitted,
            "public_redactions": len(report["redactions"]),
            "private_raw_not_rewritten": True,
        }
        (dst / "EXPORT-MANIFEST.json").write_text(
            json.dumps(export_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        sums = []
        for path in sorted(dst.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                sums.append(f"{sha(path.read_bytes())}  {path.relative_to(dst).as_posix()}")
        (dst / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
    return {"public_root": "run", "cells": len(CELLS), "private_root_modified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.raw_root), indent=2, sort_keys=True))
