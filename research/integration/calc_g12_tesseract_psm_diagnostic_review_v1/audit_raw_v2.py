"""Read-only-by-default verifier for the retained G12 PSM diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PACKAGE = Path(__file__).resolve().parent.parent / "calc_g12_tesseract_psm_diagnostic_20261004"
EXPECTED_SHA256 = "851ad8686d681fe55aaa6ac8c609e67f47812334d8ded79658434e94ff8445f8"
EXPECTED_MODES = [6, 7, 8, 10, 13]
EXPECTED_LANGUAGE = "eng"
EXPECTED_WHITELIST = "0123456789"


def audit_record(raw: dict, image: bytes) -> dict:
    errors: list[str] = []
    if not isinstance(raw, dict):
        raw = {}
        errors.append("raw record is not an object")
    digest = hashlib.sha256(image).hexdigest()
    image_record = raw.get("input", {})
    if not isinstance(image_record, dict):
        image_record = {}
        errors.append("input record is not an object")
    if digest != EXPECTED_SHA256 or digest != image_record.get("sha256"):
        errors.append("input digest")
    if len(image) != image_record.get("bytes"):
        errors.append("input byte count")
    if image_record.get("path") != "input-c2.png":
        errors.append("input path")

    if raw.get("modes") != EXPECTED_MODES:
        errors.append("frozen mode order")
    fixed = raw.get("fixed_options", {})
    if not isinstance(fixed, dict):
        fixed = {}
        errors.append("fixed-options record is not an object")
    if fixed.get("language") != EXPECTED_LANGUAGE:
        errors.append("language")
    if fixed.get("character_whitelist") != EXPECTED_WHITELIST:
        errors.append("character whitelist")

    binary = raw.get("binary", {})
    if not isinstance(binary, dict):
        binary = {}
        errors.append("binary record is not an object")
    binary_path = binary.get("path")
    if not isinstance(binary_path, str) or not binary_path.startswith("/"):
        errors.append("binary path is not an absolute recorded path")

    attempts = raw.get("attempts")
    if type(attempts) is not list or any(not isinstance(row, dict) for row in attempts):
        errors.append("attempt records are not objects")
        attempts = attempts if type(attempts) is list else []
        attempts = [row for row in attempts if isinstance(row, dict)]
    if [row.get("psm") for row in attempts] != EXPECTED_MODES:
        errors.append("attempt inventory")
    if len(attempts) != len(EXPECTED_MODES):
        errors.append("command count")

    for row, psm in zip(attempts, EXPECTED_MODES):
        expected_argv = [
            binary_path, "input-c2.png", "stdout", "--psm", str(psm),
            "-l", EXPECTED_LANGUAGE, "-c",
            f"tessedit_char_whitelist={EXPECTED_WHITELIST}",
        ]
        if row.get("argv") != expected_argv:
            errors.append(f"PSM {psm} exact argv")
        if row.get("exit_code") != 0:
            errors.append(f"PSM {psm} exit code")
        if row.get("stdout") != "551\n" or row.get("stderr") != "":
            errors.append(f"PSM {psm} output")
        start = row.get("started_monotonic_ns")
        end = row.get("ended_monotonic_ns")
        if type(start) is not int or type(end) is not int or end < start:
            errors.append(f"PSM {psm} timing fields")

    matches = [row["psm"] for row in attempts
               if row.get("exit_code") == 0 and isinstance(row.get("stdout"), str)
               and row["stdout"].strip() == "551"]
    if raw.get("candidate_modes") != matches or raw.get("disposition") != "DIAGNOSTIC_FOUND_PSM_CANDIDATE":
        errors.append("disposition consistency")
    if not isinstance(binary.get("version_stdout"), str) or not binary["version_stdout"].startswith("tesseract 5.5.2\n"):
        errors.append("binary version record")

    return {
        "disposition": "PASS_RAW_INTEGRITY_SCOPED" if not errors else "FAIL_RAW_INTEGRITY",
        "errors": errors,
        "input_sha256": digest,
        "attempts": len(attempts),
        "exact_match_modes": matches,
        "scope": "raw-command/output integrity only; does not validate unseen OCR accuracy",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=PACKAGE / "RAW.json")
    parser.add_argument("--input", type=Path, default=PACKAGE / "input-c2.png")
    parser.add_argument("--compare-retained", action="store_true",
                        help="compare the computed report with the preserved AUDIT.json")
    parser.add_argument("--retained-audit", type=Path, default=PACKAGE / "AUDIT.json")
    parser.add_argument("--write-audit", type=Path,
                        help="write a new report to this path; existing paths are never replaced")
    args = parser.parse_args(argv)

    try:
        raw = json.loads(args.raw.read_text(encoding="utf-8"))
        image = args.input.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"disposition": "FAIL_RAW_INTEGRITY", "errors": [str(exc)]}, sort_keys=True))
        return 1

    report = audit_record(raw, image)
    retained_matches = True
    if args.compare_retained:
        try:
            retained = json.loads(args.retained_audit.read_text(encoding="utf-8"))
            retained_matches = retained == report
        except (OSError, UnicodeError, json.JSONDecodeError):
            retained_matches = False
        if not retained_matches:
            report["errors"].append("retained audit differs from computed report")
            report["disposition"] = "FAIL_RAW_INTEGRITY"

    if args.write_audit is not None:
        try:
            with args.write_audit.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(report, indent=2) + "\n")
        except FileExistsError:
            print(json.dumps({**report, "errors": report["errors"] + ["output exists; refusing replacement"]}, sort_keys=True))
            return 1
        except OSError as exc:
            print(json.dumps({**report, "errors": report["errors"] + [str(exc)]}, sort_keys=True))
            return 1

    print(json.dumps(report, sort_keys=True))
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
