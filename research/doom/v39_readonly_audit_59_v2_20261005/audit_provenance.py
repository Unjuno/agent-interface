"""Read-only cross-check of the A02 freeze, archive, and saved output."""
import hashlib
import json
from pathlib import Path
import subprocess


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(commit, relative):
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO, check=True, capture_output=True).stdout


def manifest_rows(raw):
    rows = {}
    for line in raw.decode("utf-8").splitlines():
        if not line:
            continue
        expected, separator, relative = line.partition("  ")
        if not separator or len(expected) != 64 or relative in rows:
            raise ValueError(f"invalid or duplicate SHA256SUMS row: {line!r}")
        rows[relative] = expected
    return rows


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    correction = json.loads((PACKAGE / "CORRECTIONS.json").read_text(encoding="utf-8"))
    result = json.loads((PACKAGE / "MUTABILITY_RESULT_A02.json").read_text(encoding="utf-8"))
    runs = json.loads((PACKAGE / "RUNS.json").read_text(encoding="utf-8"))
    errors = []
    archive = REPO / freeze["source_archive_path"]
    source_commit = freeze["source_archive_commit"]
    source_manifest_path = freeze["source_archive_path"] + "/SHA256SUMS"
    try:
        frozen_manifest_raw = git_blob(source_commit, source_manifest_path)
        if hashlib.sha256(frozen_manifest_raw).hexdigest() != freeze["source_archive_sha256s_sha256"]:
            errors.append("frozen Git-tree SHA256SUMS identity mismatch")
        frozen_rows = manifest_rows(frozen_manifest_raw)
    except (subprocess.CalledProcessError, ValueError) as error:
        frozen_rows = {}
        errors.append(f"cannot verify frozen Git-tree manifest: {error}")

    for relative, expected in freeze["source_archive_members"].items():
        git_path = freeze["source_archive_path"] + "/" + relative
        try:
            frozen_bytes = git_blob(source_commit, git_path)
            if hashlib.sha256(frozen_bytes).hexdigest() != expected:
                errors.append(f"frozen Git-tree member hash mismatch: {relative}")
        except subprocess.CalledProcessError:
            errors.append(f"frozen Git-tree member missing: {relative}")
        path = (archive / relative).resolve()
        if archive.resolve() not in path.parents or not path.is_file():
            errors.append(f"source archive member missing or escaping: {relative}")
        elif digest(path) != expected:
            errors.append(f"source archive member hash mismatch: {relative}")
        if frozen_rows.get(relative) != expected:
            errors.append(f"frozen Git-tree manifest row mismatch: {relative}")

    # The parent PR appended its source-replay and unit-test receipts to the
    # same evidence directory after A02. Keep them distinct from the frozen run.
    appended = {
        "raw/PARENT_SYNC.exit.txt",
        "raw/PARENT_SYNC.json",
        "raw/PARENT_SYNC.stdout",
        "raw/UNIT_TESTS.exit.txt",
        "raw/UNIT_TESTS.json",
        "raw/UNIT_TESTS.stdout",
        "run_current_parent_projection.py",
    }
    try:
        current_rows = manifest_rows((archive / "SHA256SUMS").read_bytes())
        actual = {
            path.relative_to(archive).as_posix()
            for path in archive.rglob("*") if path.is_file() and
            "__pycache__" not in path.parts
        } - {"SHA256SUMS"}
        if actual != set(current_rows):
            errors.append("current source archive inventory differs from SHA256SUMS")
        if not set(freeze["source_archive_members"]).issubset(current_rows):
            errors.append("current manifest omits one or more frozen source members")
        for relative, expected in current_rows.items():
            if not (archive / relative).is_file() or digest(archive / relative) != expected:
                errors.append(f"current source archive manifest mismatch: {relative}")
        extra = set(current_rows) - set(freeze["source_archive_members"])
        if extra != appended:
            errors.append(f"current parent-sync append set mismatch: {sorted(extra)}")
    except (OSError, ValueError) as error:
        errors.append(f"cannot verify current source archive manifest: {error}")

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
        "current_archive_members_verified": len(current_rows) if "current_rows" in locals() else 0,
        "post_freeze_parent_sync_members": len(appended),
        "source_files_pinned": len(freeze["source_sha256"]),
        "run_commands": len(runs.get("runs", [])),
        "a02_result": result.get("status"),
        "scope": "saved construction provenance and archive integrity only",
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
