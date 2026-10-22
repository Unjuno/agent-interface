"""Independent, read-only checks for RAW.json and the retained input bytes."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parent
RAW_PATH = ROOT / "RAW.json"
INPUT_PATH = ROOT / "input-c2.png"
AUDIT_PATH = ROOT / "AUDIT.json"
EXPECTED_SHA256 = "851ad8686d681fe55aaa6ac8c609e67f47812334d8ded79658434e94ff8445f8"
EXPECTED_MODES = [6, 7, 8, 10, 13]


def main() -> int:
    if AUDIT_PATH.exists():
        raise SystemExit("refusing to replace existing AUDIT.json")
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    data = INPUT_PATH.read_bytes()
    errors: list[str] = []
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256 or digest != raw.get("input", {}).get("sha256"):
        errors.append("input digest")
    if len(data) != raw.get("input", {}).get("bytes"):
        errors.append("input byte count")
    if raw.get("modes") != EXPECTED_MODES:
        errors.append("frozen mode order")
    attempts = raw.get("attempts")
    if type(attempts) is not list or [x.get("psm") for x in attempts] != EXPECTED_MODES:
        errors.append("attempt inventory")
        attempts = attempts if type(attempts) is list else []

    commands = [x.get("argv", []) for x in attempts]
    if len(commands) == len(EXPECTED_MODES):
        normalized = [tuple(arg for i, arg in enumerate(argv) if i != 4) for argv in commands]
        if len(set(normalized)) != 1:
            errors.append("non-PSM argv changed")
        if any(len(argv) != 9 or argv[4] != str(psm) for argv, psm in zip(commands, EXPECTED_MODES)):
            errors.append("argv shape or PSM binding")
    else:
        errors.append("command count")

    for row in attempts:
        if row.get("exit_code") != 0:
            errors.append(f"PSM {row.get('psm')} exit code")
        if row.get("stdout") != "551\n" or row.get("stderr") != "":
            errors.append(f"PSM {row.get('psm')} output")
        if type(row.get("started_monotonic_ns")) is not int or type(row.get("ended_monotonic_ns")) is not int or row["ended_monotonic_ns"] < row["started_monotonic_ns"]:
            errors.append(f"PSM {row.get('psm')} timing fields")

    matches = [x["psm"] for x in attempts if x.get("exit_code") == 0 and x.get("stdout", "").strip() == "551"]
    if raw.get("candidate_modes") != matches or raw.get("disposition") != "DIAGNOSTIC_FOUND_PSM_CANDIDATE":
        errors.append("disposition consistency")
    binary = raw.get("binary", {})
    if not binary.get("version_stdout", "").startswith("tesseract 5.5.2\n"):
        errors.append("binary version record")

    audit = {
        "disposition": "PASS_RAW_INTEGRITY_SCOPED" if not errors else "FAIL_RAW_INTEGRITY",
        "errors": errors,
        "input_sha256": digest,
        "attempts": len(attempts),
        "exact_match_modes": matches,
        "scope": "raw-command/output integrity only; does not validate unseen OCR accuracy",
    }
    AUDIT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
