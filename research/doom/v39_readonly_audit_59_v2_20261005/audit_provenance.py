"""Read-only cross-check of the A02 freeze, archive, and saved output."""
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    correction = json.loads((PACKAGE / "CORRECTIONS.json").read_text(encoding="utf-8"))
    result = json.loads((PACKAGE / "MUTABILITY_RESULT_A02.json").read_text(encoding="utf-8"))
    runs = json.loads((PACKAGE / "RUNS.json").read_text(encoding="utf-8"))
    errors = []
    archive = REPO / freeze["source_archive_path"]
    if digest(archive / "SHA256SUMS") != freeze["source_archive_sha256s_sha256"]:
        errors.append("source archive SHA256SUMS identity mismatch")
    for relative, expected in freeze["source_archive_members"].items():
        path = (archive / relative).resolve()
        if archive.resolve() not in path.parents or not path.is_file():
            errors.append(f"source archive member missing or escaping: {relative}")
        elif digest(path) != expected:
            errors.append(f"source archive member hash mismatch: {relative}")

    for name, expected in freeze["source_sha256"].items():
        actual = digest(PACKAGE / name)
        if name == "README.md":
            if (expected != correction["frozen_pre_run_sha256"] or
                    actual != correction["corrected_sha256"]):
                errors.append("README correction is not accounted for")
        elif actual != expected:
            errors.append(f"frozen executable source changed: {name}")

    result_sources = result.get("source_sha256", {})
    pairs = {
        "readonly_auditor": "audit_readonly_v2.py",
        "probe_runner": "probe_legacy_mutation.py",
        "test_module": "test_readonly_audit.py",
    }
    for result_name, source_name in pairs.items():
        if result_sources.get(result_name) != freeze["source_sha256"].get(source_name):
            errors.append(f"result source pin mismatch: {source_name}")
    if result.get("experiment_id") != freeze.get("experiment_id"):
        errors.append("result experiment identity mismatch")
    if result.get("status") != "PASS_V1_MUTATION_REPRODUCED_V2_READ_ONLY":
        errors.append("A02 result disposition mismatch")
    if result.get("legacy_auditor", {}).get("changed_files") != ["raw/AUDIT.json"]:
        errors.append("V1 changed-file result mismatch")
    if not result.get("readonly_v2", {}).get("archive_bytes_unchanged"):
        errors.append("V2 archive preservation result mismatch")
    if any(row.get("exit_code") != 0 for row in runs.get("runs", [])):
        errors.append("one or more frozen run commands failed")
    if len(runs.get("runs", [])) != 4:
        errors.append("run log command count mismatch")

    print(json.dumps({
        "status": "PASS_A02_PROVENANCE_AUDIT" if not errors else
                  "FAIL_A02_PROVENANCE_AUDIT",
        "errors": errors,
        "archive_members_verified": len(freeze["source_archive_members"]),
        "source_files_pinned": len(freeze["source_sha256"]),
        "run_commands": len(runs.get("runs", [])),
        "a02_result": result.get("status"),
        "scope": "saved construction provenance and archive integrity only",
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
