from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[3]
COMMIT = "6b3c5fd93671c87fa02065da64afb397e7cdf62c"
PREFIX = "research/analysis/resident_gtk_effect_binding_3642_v1"


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{COMMIT}:{path}"])


def git_paths(prefix: str) -> list[str]:
    raw = subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "-r", "-z", "--name-only", COMMIT, "--", prefix])
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_sums(data: bytes) -> list[tuple[str, str]]:
    records = []
    for number, raw_line in enumerate(data.decode("utf-8").splitlines(), 1):
        fields = raw_line.split(None, 1)
        if len(fields) != 2 or len(fields[0]) != 64:
            raise ValueError(f"malformed SHA256SUMS line {number}")
        records.append((fields[0], fields[1]))
    return records


def main() -> int:
    evidence_prefix = f"{PREFIX}/evidence"
    tree_paths = set(git_paths(evidence_prefix))
    sums_path = f"{evidence_prefix}/SHA256SUMS"
    sums_bytes = git_bytes(sums_path)
    records = parse_sums(sums_bytes)
    checks = []
    for expected, relative in records:
        path = f"{PREFIX}/{relative}"
        if path not in tree_paths:
            checks.append({"path": relative, "expected_sha256": expected, "status": "MISSING_FROM_GIT_TREE"})
            continue
        data = git_bytes(path)
        actual = sha256(data)
        checks.append({"path": relative, "expected_sha256": expected, "actual_sha256": actual,
                       "status": "MATCH" if actual == expected else "HASH_MISMATCH", "bytes": len(data)})

    with tempfile.TemporaryDirectory(prefix="issue3655-gitblob-") as temp:
        temp_root = Path(temp)
        evidence_root = temp_root / "evidence"
        for path in sorted(tree_paths):
            relative = path.removeprefix(evidence_prefix + "/")
            destination = evidence_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(git_bytes(path))
        auditor_path = f"{PREFIX}/audit.py"
        local_auditor = temp_root / "audit.py"
        local_auditor.write_bytes(git_bytes(auditor_path))
        audit_run = subprocess.run([sys.executable, str(local_auditor), str(evidence_root), str(temp_root / "audit-out")],
                                   capture_output=True, text=True, check=False)
        try:
            audit_json = json.loads((temp_root / "audit-out" / "AUDIT.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            audit_json = None

    missing = [item["path"] for item in checks if item["status"] == "MISSING_FROM_GIT_TREE"]
    mismatched = [item["path"] for item in checks if item["status"] == "HASH_MISMATCH"]
    complete = not missing and not mismatched and audit_json is not None and not audit_json.get("failures")
    result = {
        "issue": 3655,
        "predecessor_issue": 3642,
        "source_commit": COMMIT,
        "source_tree": git_paths(PREFIX),
        "evidence_tree_file_count": len(tree_paths),
        "sha256sums_git_blob_sha256": sha256(sums_bytes),
        "listed_artifact_count": len(records),
        "artifact_checks": checks,
        "missing_paths": missing,
        "hash_mismatches": mismatched,
        "auditor_git_blob_sha256": sha256(git_bytes(auditor_path)),
        "auditor_return_code": audit_run.returncode,
        "auditor_stdout": audit_run.stdout.strip(),
        "auditor_stderr": audit_run.stderr.strip(),
        "auditor_result": audit_json,
        "data_integrity_decision": "PASS_COMMITTED_EVIDENCE_REPRODUCES" if complete else "HOLD_COMMITTED_ARTIFACTS_INCOMPLETE",
        "container_execution": "STOP_CONTAINER_UNAVAILABLE",
        "container_claimed": False,
        "formal_allocation_rerun": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
