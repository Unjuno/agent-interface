"""Verify the additive r87 custody manifest against a checked-out repository."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REPORT = HERE / "CUSTODY_CORRECTED_MANIFEST_20261104.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    errors = []
    source_manifest = REPO / report["source_attempt_manifest"]
    source_freeze = REPO / report["source_freeze"]
    if sha256(source_manifest) != report["source_manifest_sha256"]:
        errors.append("original attempt manifest digest mismatch")
    if sha256(source_freeze) != report["source_freeze_sha256"]:
        errors.append("source-freeze digest mismatch")
    attempt_root = REPO / report["source_attempt_manifest"].rsplit("/", 1)[0]
    counts = {"verified_original_bytes": 0, "available_hash_mismatch": 0,
              "original_bytes_unrecovered": 0}
    for row in report["files"]:
        path = attempt_root / row["path"]
        disposition = row["disposition"]
        if disposition == "original_bytes_unrecovered":
            counts[disposition] += 1
            if path.exists():
                errors.append(f"unavailable path now exists: {row['path']}")
            continue
        if not path.is_file():
            errors.append(f"listed retained file is missing: {row['path']}")
            continue
        actual_sha = sha256(path)
        actual_bytes = path.stat().st_size
        if actual_sha != row["current_sha256"] or actual_bytes != row["current_bytes"]:
            errors.append(f"recorded current digest/length changed: {row['path']}")
        if disposition == "verified_original_bytes":
            counts[disposition] += 1
            if actual_sha != row["expected_sha256"] or actual_bytes != row["expected_bytes"]:
                errors.append(f"original expected bytes do not verify: {row['path']}")
        elif disposition == "available_hash_mismatch":
            counts[disposition] += 1
            if actual_sha == row["expected_sha256"]:
                errors.append(f"mismatch disposition is stale: {row['path']}")
        else:
            errors.append(f"unknown disposition: {disposition}")
    summary = {"schema": report["schema"], "counts": counts,
               "manifest_entries": len(report["files"]), "errors": errors,
               "status": "PASS_CUSTODY_MAP" if not errors else "FAIL"}
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())