#!/usr/bin/env python3
"""Independent raw-only auditor; intentionally imports neither runner nor fixture."""
import argparse
import base64
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_pixels(pattern: str, width: int, height: int) -> list[int]:
    colors = {
        "all_zero": [0x00000000],
        "ascii_and_utf8": [0x00434241, 0x000080C2],
        "high_non_utf8": [0x00FF0000],
        "mixed": [0x00434241, 0x00FF0000, 0x000080C2, 0x00123456],
        "ordinary_color": [0x00123456, 0x006AAACC, 0x00FEDCBA, 0x00010203],
        "construction_ascii": [0x00434241, 0x000080C2],
        "construction_non_utf8": [0x00FF0011],
    }
    palette = colors[pattern]
    return [palette[(x + y * width) % len(palette)] for y in range(height) for x in range(width)]


def expected_schedule(directory: Path) -> dict[str, dict]:
    schedule = json.loads((directory / "SCHEDULE.json").read_text(encoding="utf-8"))
    cases = {}
    index = 0
    for repetition in schedule["repetitions"]:
        for pattern in schedule["patterns"]:
            for target in schedule["targets"]:
                case_id = f"{repetition:02d}-{pattern}-{target}"
                cases[case_id] = {
                    "index": index,
                    "repetition": repetition,
                    "pattern": pattern,
                    "target": target,
                    "width": schedule["width"],
                    "height": schedule["height"],
                }
                index += 1
    return cases


def validate(directory: Path) -> dict:
    raw_path = directory / "raw.jsonl"
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    raw_bytes = raw_path.read_bytes()
    errors = []
    cases = expected_schedule(directory)
    if sha256(raw_bytes) != summary.get("raw_sha256"):
        errors.append("raw_sha256")
    rows = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines()]
    if len(rows) != len(cases):
        errors.append("row_count")
    found = [row.get("case", {}).get("case_id") for row in rows]
    if set(found) != set(cases) or len(found) != len(set(found)):
        errors.append("case_id_set")

    string_rows = legacy_errors = byte_rows = candidate_mismatches = pixel_mismatches = 0
    for row in rows:
        case = row.get("case", {})
        case_id = case.get("case_id")
        spec = cases.get(case_id)
        if spec is None:
            errors.append(f"unknown_case:{case_id}")
            continue
        for key, value in spec.items():
            if case.get(key) != value:
                errors.append(f"schedule:{case_id}:{key}")
        if row.get("status") != "COMPLETE":
            errors.append(f"status:{case_id}")
        if not row.get("cleanup_complete") or row.get("fixture_exit") != 0 or row.get("xvfb_exit") != 0:
            errors.append(f"process_cleanup:{case_id}")
        if row.get("tcp_listening") is not False or row.get("xauthority_mode") != "0o600":
            errors.append(f"display_isolation:{case_id}")
        width, height = spec["width"], spec["height"]
        geometry = row.get("geometry", {})
        if (geometry.get("width"), geometry.get("height"), geometry.get("depth")) != (width, height, 24):
            errors.append(f"geometry:{case_id}")
        if geometry.get("bits_per_pixel") not in (24, 32) or geometry.get("bytes_per_line", 0) < width * 3:
            errors.append(f"stride:{case_id}")

        kind = row.get("python_data_type")
        try:
            candidate = base64.b64decode(row["candidate_bytes_b64"], validate=True)
            native = base64.b64decode(row["native_bytes_b64"], validate=True)
            representation = base64.b64decode(row["representation_b64"], validate=True)
        except Exception:
            errors.append(f"base64:{case_id}")
            continue
        if kind == "str":
            string_rows += 1
            text = row.get("python_data_text")
            if not isinstance(text, str) or row.get("python_data_bytes_b64") is not None:
                errors.append(f"string_representation:{case_id}")
                continue
            source_bytes = text.encode("UTF-8")
            legacy_error = row.get("legacy_error") or {}
            if legacy_error.get("type") != "TypeError" or row.get("legacy_bytes_b64") is not None:
                errors.append(f"legacy_string_behavior:{case_id}")
            else:
                legacy_errors += 1
        elif kind == "bytes":
            byte_rows += 1
            if row.get("python_data_text") is not None or row.get("legacy_error") is not None:
                errors.append(f"byte_representation:{case_id}")
                continue
            try:
                source_bytes = base64.b64decode(row["python_data_bytes_b64"], validate=True)
                legacy = base64.b64decode(row["legacy_bytes_b64"], validate=True)
            except Exception:
                errors.append(f"byte_base64:{case_id}")
                continue
            if legacy != source_bytes:
                errors.append(f"legacy_bytes_changed:{case_id}")
        else:
            errors.append(f"python_data_type:{case_id}")
            continue
        if representation != source_bytes or candidate != source_bytes:
            errors.append(f"normalization:{case_id}")
        if native != candidate:
            candidate_mismatches += 1
            errors.append(f"native_bytes:{case_id}")
        if sha256(source_bytes) != row.get("representation_sha256") or sha256(candidate) != row.get("candidate_sha256") or sha256(native) != row.get("native_sha256"):
            errors.append(f"byte_hash:{case_id}")
        if len(native) != geometry.get("bytes_per_line", -1) * height:
            errors.append(f"native_length:{case_id}")
        expected = expected_pixels(spec["pattern"], width, height)
        if row.get("source_pixels") != expected or row.get("native_pixels") != expected:
            pixel_mismatches += 1
            errors.append(f"source_pixel_oracle:{case_id}")

    if summary.get("scheduled") != len(cases) or summary.get("completed") != len(rows) or summary.get("failed") != 0:
        errors.append("summary_counts")
    if summary.get("string_payloads") != string_rows or summary.get("bytes_payloads") != byte_rows:
        errors.append("summary_types")
    if summary.get("legacy_type_errors") != legacy_errors:
        errors.append("summary_legacy_errors")
    if summary.get("candidate_native_mismatches") != candidate_mismatches:
        errors.append("summary_native_mismatch_count")
    if summary.get("pixel_oracle_mismatches") != pixel_mismatches:
        errors.append("summary_pixel_mismatch_count")

    if errors:
        decision = "FAIL_RAW_AUDIT"
    elif string_rows == 0:
        decision = "HOLD_NO_LIVE_STRING8_DISCRIMINATOR"
    elif legacy_errors == 0 or candidate_mismatches:
        decision = "FAIL_X11_STRING8_NORMALIZATION"
    else:
        decision = "PASS_X11_STRING8_NORMALIZATION_BOUNDARY_SCOPED"
    return {
        "decision": decision,
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "checks": 18,
        "errors": errors,
        "rows": len(rows),
        "string_payloads": string_rows,
        "bytes_payloads": byte_rows,
        "legacy_type_errors": legacy_errors,
        "input_sha256": sha256(raw_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate(args.evidence)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
