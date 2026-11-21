"""Audit the retained WSL TCP-only Xvfb attempt."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[3]


def manifest_hash(path: Path, relative: str) -> str:
    data = path.read_bytes()
    if not relative.endswith(".bin"):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def verify_manifest() -> int:
    manifest = ROOT / "SHA256SUMS"
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in expected:
            raise SystemExit(f"duplicate manifest path: {relative}")
        expected[relative] = digest
    excluded = {"SHA256SUMS", "audit.json", "audit-final.stdout.log",
                "audit-final.exit-code.txt", ".gitattributes", "audit_packet.py"}
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
              if path.is_file() and path.relative_to(ROOT).as_posix() not in excluded
              and "__pycache__" not in path.relative_to(ROOT).parts
              and path.suffix != ".pyc"}
    if actual != set(expected):
        raise SystemExit("manifest file-set mismatch")
    for relative, digest in expected.items():
        if manifest_hash(ROOT / Path(*relative.split("/")), relative) != digest:
            raise SystemExit(f"manifest checksum mismatch: {relative}")
    return len(expected)


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    for relative in conditions["source_files"]:
        pinned = subprocess.check_output(
            ["git", "rev-parse", f"{conditions['source_revision']}:{relative}"],
            cwd=REPO_ROOT, text=True).strip()
        actual = subprocess.check_output(
            ["git", "hash-object", f"--path={relative}",
             str(REPO_ROOT / relative)], cwd=REPO_ROOT, text=True).strip()
        if pinned != actual:
            raise SystemExit(f"source drift: {relative}")
    run = ROOT / "runs" / "normal"
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    exit_code = int((run / "exit-code.txt").read_text(encoding="utf-8").strip())
    if (exit_code != 1 or result.get("status") != "FAIL" or
            result.get("error") != "missing or ambiguous X-Resource process identity" or
            result.get("disconnect_receipt") is not None or
            result.get("initial_held_readback") is not None or
            result.get("final_cleanup_status") != "key_release_sync_completed" or
            result.get("final_key_down") != {"a": False, "b": False}):
        raise SystemExit("retained WSL transport-failure classification drift")
    audit = {
        "status": "PASS_AUDIT_HOLD_TRANSPORT_IDENTITY",
        "source_revision": conditions["source_revision"],
        "source_files_checked": len(conditions["source_files"]),
        "attempts_run": 1,
        "normal_attempt_exit_code": exit_code,
        "xres_disconnect_observed": False,
        "held_key_readback_observed": False,
        "final_keys_up": True,
        "optimized_attempt": "not-run-after-deterministic-transport-identity-hold",
        "manifest_files_verified": verify_manifest(),
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
