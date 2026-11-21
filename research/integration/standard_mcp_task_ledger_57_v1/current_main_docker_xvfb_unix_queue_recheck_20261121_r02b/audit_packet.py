from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[3]


def digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8-sig"))
    source_rows = (ROOT / "source-blobs.txt").read_text(encoding="utf-8").splitlines()
    source_hashes = {}
    for row in source_rows:
        expected, relative = row.split("  ", 1)
        source = ROOT / Path(*relative.split("/"))
        source_path = relative.removeprefix("source/")
        actual = subprocess.check_output(["git", "hash-object", "--path=" + source_path, str(source)], cwd=REPO_ROOT, text=True).strip()
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {relative}")
        pinned = subprocess.check_output(["git", "rev-parse", f"{conditions['source_revision']}:{source_path}"], cwd=REPO_ROOT, text=True).strip()
        if pinned != expected:
            raise SystemExit(f"pinned revision mismatch: {relative}")
        source_hashes[relative] = expected
    runs = {}
    for mode in ("normal", "optimized"):
        folder = ROOT / "runs" / mode
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        code = int((folder / "exit-code.txt").read_text(encoding="ascii").strip())
        if code != 0 or result.get("status") != "PASS_SCOPED_XVFB_HELD_KEY_ORDER":
            raise SystemExit(f"{mode} attempt did not pass scoped preconditions")
        if result.get("disconnect_receipt", {}).get("status") != "disconnected":
            raise SystemExit(f"{mode} lacks XRes disconnect receipt")
        if result.get("initial_held_readback", {}).get("keys_down") != {"a": True, "b": False}:
            raise SystemExit(f"{mode} initial held-key readback mismatch")
        if result.get("independent_release_effect_observed") is not True:
            raise SystemExit(f"{mode} independent release missing")
        if result.get("late_keypress_observed") is not False:
            raise SystemExit(f"{mode} delayed KeyPress observed or ambiguous")
        if result.get("late_keypress_readback", {}).get("keys_down") != {"a": False, "b": False}:
            raise SystemExit(f"{mode} horizon readback mismatch")
        if result.get("final_key_down") != {"a": False, "b": False}:
            raise SystemExit(f"{mode} final cleanup did not release both keys")
        if result.get("owner_returncode") != -15 or result.get("owner_stderr") != "":
            raise SystemExit(f"{mode} owner termination evidence mismatch")
        runs[mode] = {
            "exit_code": code,
            "late_keypress_observed": False,
            "initial_a_down": True,
            "state_after_disconnect_a_down": result["state_after_disconnect_before_release"]["keys_down"]["a"],
            "independent_release_effect_observed": True,
            "final_keys_up": True,
            "server_sha256": result["server_build_provenance"]["sha256"],
            "server_package": result["server_build_provenance"]["packages"]["xvfb"]["stdout"],
        }
    excluded = {"SHA256SUMS", "audit.json", "audit.stdout.log", "audit.exit-code.txt", "audit_packet.py"}
    actual_files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in excluded and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    expected = {}
    for row in (ROOT / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        checksum, relative = row.split("  ", 1)
        expected[relative] = checksum
    if actual_files != set(expected):
        raise SystemExit("manifest file set mismatch")
    for relative, checksum in expected.items():
        if digest(ROOT / Path(*relative.split("/"))) != checksum:
            raise SystemExit(f"manifest checksum mismatch: {relative}")
    audit = {
        "status": "PASS_SCOPED_XVFB_QUEUE_RECHECK",
        "attempt_id": conditions["attempt_id"],
        "source_hashes": source_hashes,
        "runs": runs,
        "manifest_files_verified": len(expected),
        "interpretation": "No late synthetic KeyPress was observed 8.5 s after owner termination in either run; independent release transition and final all-keys-up were observed.",
        "scope_limit": "Synthetic XTEST/Xvfb only; does not prove standard MCP caller, production owner recovery, GUI task effect, live MAP01, efficiency, or reliability rate.",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
