#!/usr/bin/env python3
"""Independent full-table reconstruction for the retained A01 raw replay.

This auditor does not import candidate.py or production guard code. It rebuilds
every evaluated row from the immutable manual readout and frozen guard rule,
then compares the complete expected table with the retained one-shot raw.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
INPUT = PACKAGE / "input/VISUAL_READOUT.json"
FREEZE = HERE / "FREEZE.json"
PARENT_FREEZE = PACKAGE / "FREEZE.json"
RAW = PACKAGE / "raw.json"
EXPECTED_INPUT_SHA256 = "610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724"
EXPECTED_VIDEO_SHA256 = "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(readout, freeze):
    """Recompute the complete bounded guard trace using scalar arithmetic."""
    rows = readout.get("samples")
    if type(rows) is not list or len(rows) != freeze["source_readout_sample_count"]:
        raise ValueError("manual readout sample count mismatch")
    source_clock = freeze["source_game_time_s"]
    source_health = freeze["source_health"]
    critical_floor = freeze["critical_health_minimum"]
    max_age_s = freeze["max_source_age_ms"] / 1000
    pending_last = freeze["model_pending_last_sample_game_s"]
    first_local = freeze["first_local_plan_sample_game_s"]
    results = []

    for loss in freeze["thresholds"]:
        hard_floor = max(critical_floor, source_health - loss)
        evaluated = []
        first = None
        for row in rows:
            game_time = float(row["game_clock"].removesuffix("s"))
            if game_time <= source_clock:
                continue
            health = row["health"]
            age = game_time - source_clock
            if age > max_age_s:
                status, reason = "UNKNOWN", "source_expired"
            elif health < hard_floor:
                status, reason = "HARD_INVALIDATED", "below_hard_minimum"
            elif health == source_health:
                status, reason = "UNCHANGED", "signal_unchanged"
            else:
                status, reason = "SOFT_CHANGED", "within_validity_envelope"
            sample = {
                "game_time_s": game_time,
                "health": health,
                "phase": row["phase"],
                "status": status,
                "reason": reason,
                "hard_minimum": hard_floor,
            }
            evaluated.append(sample)
            if status in {"HARD_INVALIDATED", "UNKNOWN"}:
                first = sample
                break
        results.append({
            "maximum_health_loss": loss,
            "hard_minimum": hard_floor,
            "first_invalidation": first if first and first["status"] == "HARD_INVALIDATED" else None,
            "evaluated_samples": evaluated,
        })
    return results, pending_last, first_local


def validate_sweep(actual, expected):
    """Reject any changed, missing, reordered, or extra row or field."""
    if actual != expected:
        raise ValueError("complete_sweep_reconstruction_mismatch")


def audit(raw_path):
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    parent_freeze = json.loads(PARENT_FREEZE.read_text(encoding="utf-8"))
    readout = json.loads(INPUT.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    input_sha = digest(INPUT)
    if input_sha != EXPECTED_INPUT_SHA256:
        errors.append("input_sha256_mismatch")
    if digest(HERE / "audit.py") != freeze.get("auditor_sha256"):
        errors.append("auditor_sha256_mismatch")
    if raw.get("schema") != "astra-health-guard-replay-a01-v1":
        errors.append("raw_schema_mismatch")
    if raw.get("input_sha256") != input_sha:
        errors.append("raw_input_sha256_mismatch")
    if raw.get("controller_sha256") != parent_freeze.get("controller_source_sha256"):
        errors.append("raw_controller_sha256_mismatch")
    if raw.get("guard_sha256") != parent_freeze.get("guard_source_sha256"):
        errors.append("raw_guard_sha256_mismatch")
    if raw.get("source_video_sha256") != EXPECTED_VIDEO_SHA256:
        errors.append("raw_video_sha256_mismatch")
    if raw.get("source_readout_sample_count") != len(readout["samples"]):
        errors.append("raw_readout_sample_count_mismatch")
    if digest(raw_path) != freeze["source_sha256"]["raw.json"]:
        errors.append("raw_sha256_mismatch")
    try:
        expected, pending_last, first_local = reconstruct(readout, freeze)
        try:
            validate_sweep(raw.get("sweep"), expected)
        except ValueError as error:
            errors.append(str(error))
        first_times = {
            item["maximum_health_loss"]: (item["first_invalidation"] or {}).get("game_time_s")
            for item in expected
        }
        before_pending = {
            loss: (time is not None and time <= pending_last)
            for loss, time in first_times.items()
        }
        if before_pending != {3: True, 4: True, 5: True, 6: False, 12: False}:
            errors.append("pending_boundary_reconstruction_mismatch")
        if first_times != {3: 47.0, 4: 54.8, 5: 54.8, 6: 56.4, 12: 56.4}:
            errors.append("first_crossing_reconstruction_mismatch")
        if first_local != 56.4:
            errors.append("frozen_local_plan_boundary_mismatch")
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"input_reconstruction_error:{type(error).__name__}")
        expected = []

    return {
        "schema": "astra-health-guard-replay-a02-audit-v1",
        "status": "PASS_FULL_TABLE_RECONSTRUCTION" if not errors else "FAIL_FULL_TABLE_RECONSTRUCTION",
        "errors": errors,
        "raw_sha256": digest(raw_path),
        "input_sha256": input_sha,
        "auditor_sha256": digest(HERE / "audit.py"),
        "threshold_rows_reconstructed": len(expected),
        "evaluated_rows_reconstructed": sum(len(row["evaluated_samples"]) for row in expected),
        "scope": "readout-to-raw arithmetic reconstruction only; no candidate rerun, live V39 session, or gameplay result",
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json NEW_AUDIT.json")
    raw_path, output = (Path(value).resolve() for value in sys.argv[1:])
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    result = audit(raw_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
