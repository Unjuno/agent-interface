"""Reproduce the v1 audit write on a disposable archive copy and test v2."""
import hashlib
import json
import os
import platform
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
ARCHIVE = REPO / "research/doom/v39_application_consumption_conflict_59_a01_20261005"
OLD_AUDITOR = ARCHIVE / "audit_a01.py"
NEW_AUDITOR = PACKAGE / "audit_readonly_v2.py"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in root.rglob("*") if path.is_file() and
        "__pycache__" not in path.parts
    }


def clone(root, parent, name):
    destination = parent / name
    shutil.copytree(root, destination)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default=
                        "V39-READONLY-AUDIT-59-A02-V2-20261005")
    parser.add_argument("--out", type=Path,
                        default=PACKAGE / "MUTABILITY_RESULT.json")
    args = parser.parse_args()
    output = args.out if args.out.is_absolute() else PACKAGE / args.out
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite prior result: {output}")
    result = {
        "schema": "v39-readonly-audit-v2-construction-result-v1",
        "experiment_id": args.experiment_id,
        "source_archive": str(ARCHIVE.relative_to(REPO)),
        "source_archive_sha256s_sha256": sha256(ARCHIVE / "SHA256SUMS"),
        "source_sha256": {
            "readonly_auditor": sha256(NEW_AUDITOR),
            "probe_runner": sha256(Path(__file__).resolve()),
            "test_module": sha256(PACKAGE / "test_readonly_audit.py"),
        },
        "python": sys.version,
        "platform": platform.platform(),
        "legacy_auditor": {},
        "readonly_v2": {},
        "scope": "Archived-output audit behavior only; no game, model, GUI, OS input, or shared container use.",
    }
    with tempfile.TemporaryDirectory(prefix="v39-audit-readonly-v2-") as temporary:
        parent = Path(temporary)
        legacy_copy = clone(ARCHIVE, parent, "legacy")
        legacy_before = snapshot(legacy_copy)
        legacy = subprocess.run(
            [sys.executable, "-B", str(legacy_copy / "audit_a01.py")],
            cwd=legacy_copy, capture_output=True, text=True, check=False)
        legacy_after = snapshot(legacy_copy)
        changed = sorted(name for name in legacy_before
                         if legacy_before[name] != legacy_after.get(name))
        added = sorted(set(legacy_after) - set(legacy_before))
        result["legacy_auditor"] = {
            "exit_code": legacy.returncode,
            "changed_files": changed,
            "added_files": added,
            "raw_audit_sha256_before": legacy_before.get("raw/AUDIT.json"),
            "raw_audit_sha256_after": legacy_after.get("raw/AUDIT.json"),
            "stdout_disposition": json.loads(legacy.stdout).get("status")
            if legacy.stdout.strip() else None,
            "stderr": legacy.stderr,
            "write_mutation_reproduced": (
                legacy.returncode == 0 and changed == ["raw/AUDIT.json"] and
                not added and
                legacy_before.get("raw/AUDIT.json") !=
                legacy_after.get("raw/AUDIT.json")),
        }

        v2_copy = clone(ARCHIVE, parent, "readonly")
        v2_before = snapshot(v2_copy)
        v2 = subprocess.run(
            [sys.executable, "-B", str(NEW_AUDITOR), "--archive", str(v2_copy)],
            cwd=REPO, capture_output=True, text=True, check=False)
        v2_after = snapshot(v2_copy)
        try:
            v2_result = json.loads(v2.stdout)
        except json.JSONDecodeError:
            v2_result = None
        result["readonly_v2"] = {
            "exit_code": v2.returncode,
            "disposition": v2_result.get("status") if v2_result else None,
            "archive_bytes_unchanged": v2_before == v2_after,
            "added_files": sorted(set(v2_after) - set(v2_before)),
            "changed_files": sorted(name for name in v2_before
                                     if v2_before[name] != v2_after.get(name)),
            "stdout": v2.stdout,
            "stderr": v2.stderr,
        }

    result["status"] = (
        "PASS_V1_MUTATION_REPRODUCED_V2_READ_ONLY" if
        result["legacy_auditor"]["write_mutation_reproduced"] and
        result["readonly_v2"]["exit_code"] == 0 and
        result["readonly_v2"]["disposition"] == "PASS_READ_ONLY_ARCHIVE_AUDIT" and
        result["readonly_v2"]["archive_bytes_unchanged"] else
        "HOLD_CONSTRUCTION_GATE")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "legacy_changed_files": result["legacy_auditor"]["changed_files"],
        "legacy_before": result["legacy_auditor"]["raw_audit_sha256_before"],
        "legacy_after": result["legacy_auditor"]["raw_audit_sha256_after"],
        "v2_disposition": result["readonly_v2"]["disposition"],
        "v2_archive_bytes_unchanged": result["readonly_v2"]["archive_bytes_unchanged"],
        "out": str(output),
    }, sort_keys=True))
    return 0 if result["status"] == "PASS_V1_MUTATION_REPRODUCED_V2_READ_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
