import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
EXCLUDED = {"SHA256SUMS", "audit.json", "audit.stdout.log", "audit.exit-code.txt", "audit_packet.py"}


def sha(path):
    data = path.read_bytes()
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bin"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def main():
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8-sig"))
    revision = conditions["source_revision"]
    blobs = {}
    for row in (ROOT / "source-blobs.txt").read_text(encoding="ascii").splitlines():
        expected, source = row.split("  ", 1)
        actual = subprocess.check_output(["git", "rev-parse", f"{revision}:{source}"], cwd=REPO, text=True).strip()
        if actual != expected:
            raise SystemExit(f"source pin mismatch: {source}")
        blobs[source] = expected

    runs = {}
    for mode in ("normal", "optimized"):
        folder = ROOT / "runs" / mode
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        code = int((folder / "exit-code.txt").read_text(encoding="ascii").strip())
        cancel = result["cancel"]
        old = result["independent_task_oracle"]
        fresh = result["fresh_session_recovery"]["task_oracle"]
        if code != 0 or result.get("xvfb", {}).get("status") != "captured":
            raise SystemExit(f"{mode}: test exit or Xvfb provenance invalid")
        if cancel.get("owner_client_disconnect", {}).get("status") != "disconnected":
            raise SystemExit(f"{mode}: XRes disconnect missing")
        if cancel.get("owner_release_attempt", {}).get("status") != "readback_verified":
            raise SystemExit(f"{mode}: release receipt missing")
        if old.get("status") != "fail" or old.get("task_success") is not False:
            raise SystemExit(f"{mode}: old task failure was not retained")
        if fresh.get("status") != "pass" or fresh.get("task_success") is not True:
            raise SystemExit(f"{mode}: fresh-generation oracle missing")
        if cancel.get("cleanup_status") != "UNKNOWN" or cancel.get("release_confirmed") is not False or cancel.get("replay_allowed") is not False:
            raise SystemExit(f"{mode}: old-generation safety fence changed")
        if any(result["final_cleanup"]["keys_down"].values()):
            raise SystemExit(f"{mode}: final key state not neutral")
        runs[mode] = {
            "exit_code": code,
            "xres_disconnect": True,
            "release_readback_verified": True,
            "cancel_response": result.get("cancel_response", {}).get("status"),
            "old_task_effect_count": result["synthetic_application_effect"]["effect_count_at_horizon"],
            "old_task_oracle": "fail",
            "fresh_task_oracle": "pass",
            "old_generation_unknown_no_replay": True,
            "final_keys_up": True,
        }

    manifest = {}
    for row in (ROOT / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        checksum, relative = row.split("  ", 1)
        manifest[relative] = checksum
    actual_files = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path.relative_to(ROOT).as_posix() not in EXCLUDED
        and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    if actual_files != set(manifest):
        raise SystemExit("manifest file-set mismatch")
    for relative, checksum in manifest.items():
        if sha(ROOT / Path(*relative.split("/"))) != checksum:
            raise SystemExit(f"manifest checksum mismatch: {relative}")

    audit = {
        "status": "PASS_AUDIT_POSTMERGE_STANDARD_CALLER_SPLIT_OUTCOME",
        "source_revision": revision,
        "source_blobs_checked": len(blobs),
        "manifest_files_verified": len(manifest),
        "runs": runs,
        "interpretation": "Merged main reproduces bounded XRes release observation and preserves old task failure/UNKNOWN/no-replay separately from fresh-generation task success. Raw traces attribute repeated effects to A remaining held through the deliberately withheld cancellation acknowledgement; the scheduled delayed B KeyPress was not observed.",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
