#!/usr/bin/env python3
"""Independent raw-only auditor for the #4439 X11 coordinate-frame study."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path

POLICIES = {"PINNED_SCREEN", "REFRESH_SCREEN", "WINDOW_CLIENT"}
SCHEDULES = {"STABLE", "MOVE_BEFORE", "MOVE_BETWEEN"}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def decode(entry):
    if entry.get("encoding") != "base64+gzip":
        raise ValueError("unsupported image encoding")
    compressed = base64.b64decode(entry["data"], validate=True)
    if digest(compressed) != entry.get("gzip_sha256"):
        raise ValueError("compressed image digest mismatch")
    raw = gzip.decompress(compressed)
    if len(raw) != entry.get("bytes") or digest(raw) != entry.get("sha256"):
        raise ValueError("uncompressed image identity mismatch")
    return raw


def expected(policy, schedule):
    if schedule == "STABLE":
        return True
    if schedule == "MOVE_BEFORE":
        return policy != "PINNED_SCREEN"
    return policy == "WINDOW_CLIENT"


def validate(rows, mode):
    errors = []
    expected_n = 9 if mode == "construction" else 27
    if len(rows) != expected_n:
        errors.append("row_denominator")
    seen = set()
    for i, row in enumerate(rows):
        try:
            key = (row["policy"], row["schedule"], row["repetition"])
            if row["case_id"] != i:
                errors.append(f"case_order:{i}")
            if row.get("display") != 80 + i:
                errors.append(f"display_identity:{i}")
            if key in seen:
                errors.append(f"duplicate:{i}")
            seen.add(key)
            if row["policy"] not in POLICIES or row["schedule"] not in SCHEDULES:
                errors.append(f"arm:{i}")
            if row["initial_xy"] != [20, 20]:
                errors.append(f"initial_geometry:{i}")
            final_expected = [20, 20] if row["schedule"] == "STABLE" else [220, 160]
            if row["final_xy"] != final_expected:
                errors.append(f"final_geometry:{i}")
            if row["schedule"] == "STABLE":
                candidate_xy = [20, 20] if row["policy"] != "WINDOW_CLIENT" else None
            elif row["schedule"] == "MOVE_BEFORE":
                candidate_xy = [20, 20] if row["policy"] == "PINNED_SCREEN" else ([220, 160] if row["policy"] == "REFRESH_SCREEN" else None)
            else:
                candidate_xy = [20, 20] if row["policy"] != "WINDOW_CLIENT" else None
            if row["candidate_xy"] != candidate_xy:
                errors.append(f"resolved_coordinate:{i}")
            cand = decode(row["candidate_bytes"])
            oracle = decode(row["oracle_bytes"])
            background = bytes(120 * 80 * 4)
            if row.get("background_sha256") != digest(background):
                errors.append(f"background_identity:{i}")
            if row["schedule"] == "STABLE":
                if row.get("exposed_root_bytes") is not None or row.get("exposed_root_sha256") is not None:
                    errors.append(f"unexpected_exposure:{i}")
            else:
                exposed = decode(row["exposed_root_bytes"])
                if exposed != background or row.get("exposed_root_sha256") != digest(exposed):
                    errors.append(f"exposed_region:{i}")
            actual_match = cand == oracle
            if row["candidate_matches_oracle"] is not actual_match:
                errors.append(f"match_flag:{i}")
            if row["candidate_sha256"] != digest(cand) or row["oracle_sha256"] != digest(oracle):
                errors.append(f"pixel_hash:{i}")
            if row["initial_target_sha256"] != digest(oracle):
                errors.append(f"target_changed:{i}")
            if row["candidate_bytes"]["bytes"] != row["oracle_bytes"]["bytes"]:
                errors.append(f"pixel_length:{i}")
            if len(cand) != 120 * 80 * 4 or len(oracle) != len(cand):
                errors.append(f"pixel_geometry:{i}")
            t0, t1 = row["candidate_capture_ns"]
            if isinstance(t0, bool) or isinstance(t1, bool) or not isinstance(t0, int) or not isinstance(t1, int) or t1 < t0:
                errors.append(f"clock:{i}")
            if not row.get("xvfb_pid") or row.get("xvfb_returncode") != 0:
                errors.append(f"process_exit:{i}")
            for log_key in ("xvfb_stdout_sha256", "xvfb_stderr_sha256"):
                value = row.get(log_key, "")
                if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    errors.append(f"process_log_hash:{i}")
            if row.get("authority_file_mode") != "0o600":
                errors.append(f"authority_mode:{i}")
            if actual_match is not expected(row["policy"], row["schedule"]):
                errors.append(f"coordinate_outcome:{i}")
        except Exception as exc:
            errors.append(f"row:{i}:{type(exc).__name__}")
    if mode == "formal":
        required = {(p, s, r) for p in POLICIES for s in SCHEDULES for r in range(3)}
        if seen != required:
            errors.append("schedule_coverage")
    return errors


def corruption_controls(rows):
    cases = {}
    def mutate(name, fn):
        x = copy.deepcopy(rows)
        fn(x)
        cases[name] = not validate(x, "formal")
    if not rows:
        return {"unavailable": False}
    mutate("missing_row", lambda x: x.pop())
    mutate("duplicate_case", lambda x: x.__setitem__(1, copy.deepcopy(x[0])))
    mutate("wrong_policy", lambda x: x[0].update(policy="UNKNOWN"))
    mutate("wrong_schedule", lambda x: x[0].update(schedule="UNKNOWN"))
    mutate("wrong_location", lambda x: x[0].update(final_xy=[0, 0]))
    mutate("false_match_flag", lambda x: x[0].update(candidate_matches_oracle=not x[0]["candidate_matches_oracle"]))
    mutate("bad_candidate_digest", lambda x: x[0].update(candidate_sha256="0"*64))
    mutate("bad_compressed_digest", lambda x: x[0]["candidate_bytes"].update(gzip_sha256="f"*64))
    mutate("bad_bytes_count", lambda x: x[0]["oracle_bytes"].update(bytes=0))
    mutate("reversed_clock", lambda x: x[0].update(candidate_capture_ns=[9, 1]))
    mutate("wrong_exit", lambda x: x[0].update(xvfb_returncode=7))
    mutate("unsafe_authority", lambda x: x[0].update(authority_file_mode="0o644"))
    mutate("pixel_tamper", lambda x: x[0]["candidate_bytes"].update(data=base64.b64encode(gzip.compress(b"tampered", mtime=0)).decode("ascii")))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--mode", choices=("construction", "formal"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mutations", action="store_true")
    args = ap.parse_args()
    raw_bytes = Path(args.raw).read_bytes()
    rows = [json.loads(line) for line in raw_bytes.splitlines() if line]
    errors = validate(rows, args.mode)
    controls = corruption_controls(rows) if args.mutations else None
    if controls is not None and not all(controls.values()):
        errors.append("corruption_controls")
    by_cell = {}
    for row in rows:
        by_cell.setdefault((row["policy"], row["schedule"]), []).append(bool(row["candidate_matches_oracle"]))
    report = {
        "schema": "x11-region-frame-move-audit-v1", "mode": args.mode,
        "raw_sha256": digest(raw_bytes), "rows": len(rows), "errors": errors,
        "outcomes": {f"{p}/{s}": {"matches": sum(vals), "mismatches": len(vals)-sum(vals), "n": len(vals)} for (p,s), vals in sorted(by_cell.items())},
        "corruption_controls": controls,
        "passed": not errors and (controls is None or all(controls.values())),
    }
    Path(args.out).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
