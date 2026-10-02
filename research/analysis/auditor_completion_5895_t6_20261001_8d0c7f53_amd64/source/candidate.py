"""One bounded orchestrator for the preregistered eight-case Issue #5895 T6."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from matrix import make_matrix


ALLOCATION = "AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53"
TARGET_BLOB = "da805fb83f70a57ad68a0768186e214524689d40"
EXPECTED_BLOB = "3d33bda096c4c8789e183e3f864ee7626e643a7e"
FIXTURE_BLOB = "d1eb9a854cc810fa77ca173d7e2de287ee1bd64a"
TARGET_SHA256 = "f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0"
EXPECTED_SHA256 = "7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076"
FIXTURE_SHA256 = "1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    target = args.target.resolve(strict=True)
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("output directory must be absent or empty")
    out.mkdir(parents=True, exist_ok=True)

    audit_source = (target / "audit_formal_x11.py").read_bytes()
    expected_bytes = (target / "EXPECTED.json").read_bytes()
    fixture_source = (target / "test_audit_formal_x11.py").read_bytes()
    if (sha256(audit_source), sha256(expected_bytes), sha256(fixture_source)) != (
            TARGET_SHA256, EXPECTED_SHA256, FIXTURE_SHA256):
        raise SystemExit("frozen target source digest mismatch")
    sys.path.insert(0, str(target))
    old_cwd = Path.cwd()
    os.chdir(target)
    try:
        fixture_module = importlib.import_module("test_audit_formal_x11")
        baseline = fixture_module.fixture_rows()
    finally:
        os.chdir(old_cwd)

    command_sha = sha256(Path(__file__).read_bytes())
    matrix = make_matrix(baseline)
    entries = []
    all_expected = True
    for item in matrix:
        case_id = item["case_id"]
        case_dir = out / case_id
        case_dir.mkdir()
        raw_path = case_dir / "raw.jsonl"
        audit_path = case_dir / "audit.json"
        stdout_path = case_dir / "stdout.txt"
        stderr_path = case_dir / "stderr.txt"
        raw_bytes = b"".join(
            (json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
            for row in item["rows"]
        )
        raw_path.write_bytes(raw_bytes)
        completed = subprocess.run(
            [sys.executable, "-B", str(target / "audit_formal_x11.py"), str(raw_path),
             str(target / "EXPECTED.json"), str(audit_path), "synthetic-cli"],
            cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        all_expected &= completed.returncode == item["expected_exit"]
        entries.append({
            "case_id": case_id,
            "expected_exit": item["expected_exit"],
            "actual_exit": completed.returncode,
            "raw_path": f"{case_id}/raw.jsonl",
            "raw_sha256": sha256(raw_bytes),
            "audit_path": f"{case_id}/audit.json",
            "audit_sha256": sha256(audit_path.read_bytes()) if audit_path.is_file() else None,
            "stdout_path": f"{case_id}/stdout.txt",
            "stdout_sha256": sha256(stdout_path.read_bytes()),
            "stderr_path": f"{case_id}/stderr.txt",
            "stderr_sha256": sha256(stderr_path.read_bytes()),
        })
    manifest = {
        "allocation": ALLOCATION,
        "disposition": "CANDIDATE_EXPECTED" if all_expected else "CANDIDATE_MISMATCH",
        "target_git_blob": TARGET_BLOB,
        "target_sha256": sha256(audit_source),
        "expected_git_blob": EXPECTED_BLOB,
        "expected_sha256": sha256(expected_bytes),
        "fixture_git_blob": FIXTURE_BLOB,
        "fixture_sha256": sha256(fixture_source),
        "runner_sha256": command_sha,
        "cases": entries,
    }
    (out / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "disposition": manifest["disposition"],
                      "case_count": len(entries), "actual_exits": [x["actual_exit"] for x in entries]}, sort_keys=True))
    return 0 if all_expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
