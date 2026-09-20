"""Check that a published delivery-pair manifest closes over its evidence tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def audit(bundle: Path) -> dict:
    bundle = bundle.resolve()
    evidence = bundle / "evidence"
    manifest_path = evidence / "manifest.json"
    result = {
        "schema": "agent-interface/evidence-publication-closure-audit-v1",
        "result": "HOLD_MANIFEST_INVALID",
        "manifest_entries": 0,
        "present_and_matching": 0,
        "missing": [],
        "mismatched": [],
        "unlisted": [],
        "failures": [],
    }
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result["failures"].append(f"manifest unavailable or invalid: {type(exc).__name__}")
        return result

    result["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    if (not isinstance(manifest, dict) or
            manifest.get("schema") != "agent-interface/issue-3370-delivery-pair-manifest-v1" or
            manifest.get("evidence_root") != "evidence/"):
        result["failures"].append("manifest schema or evidence root is not the registered format")
        return result
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(rows, list):
        result["failures"].append("manifest files must be an array")
        return result

    result["manifest_entries"] = len(rows)
    declared: set[str] = set()
    invalid = False
    for row in rows:
        if not isinstance(row, dict):
            result["failures"].append("manifest row must be an object")
            invalid = True
            continue
        name, expected_hash, expected_bytes = row.get("path"), row.get("sha256"), row.get("bytes")
        if (not isinstance(name, str) or "\\" in name or
                PurePosixPath(name).is_absolute() or
                any(part in ("", ".", "..") for part in name.split("/")) or
                not name.startswith("evidence/") or
                not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash) or
                not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes < 0):
            result["failures"].append("manifest row has an unsafe path or invalid digest/length")
            invalid = True
            continue
        if name in declared:
            result["failures"].append(f"duplicate manifest path: {name}")
            invalid = True
            continue
        declared.add(name)
        path = bundle / PurePosixPath(name)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(bundle)
        except (OSError, ValueError):
            result["missing"].append(name)
            continue
        if path.is_symlink() or not resolved.is_file():
            result["failures"].append(f"manifest path is not a regular in-bundle file: {name}")
            invalid = True
            continue
        content = resolved.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        if len(content) != expected_bytes or actual_hash != expected_hash:
            result["mismatched"].append({
                "path": name,
                "expected_bytes": expected_bytes,
                "actual_bytes": len(content),
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
            })
        else:
            result["present_and_matching"] += 1

    actual = set()
    if evidence.exists():
        for path in evidence.rglob("*"):
            if path.is_symlink():
                result["failures"].append(f"symlink in evidence tree: {path.relative_to(bundle).as_posix()}")
                invalid = True
            elif path.is_file() and path != manifest_path and "__pycache__" not in path.parts:
                actual.add(path.relative_to(bundle).as_posix())
    result["unlisted"] = sorted(actual - declared)
    if invalid or result["failures"]:
        result["result"] = "HOLD_MANIFEST_INVALID"
    elif result["missing"]:
        result["result"] = "HOLD_PUBLICATION_GAP"
    elif result["mismatched"]:
        result["result"] = "HOLD_PUBLICATION_DRIFT"
    elif result["unlisted"]:
        result["result"] = "HOLD_UNLISTED_FILES"
    else:
        result["result"] = "PASS_PUBLICATION_CLOSED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True,
                        help="directory containing evidence/manifest.json")
    parser.add_argument("--output", type=Path, required=True,
                        help="write the audit receipt outside the frozen evidence tree")
    args = parser.parse_args()
    result = audit(args.bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS_PUBLICATION_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
