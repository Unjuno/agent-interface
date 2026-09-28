"""Validate the retained output shape of the Issue #5206 host microbenchmarks."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


HASH_RE = re.compile(r"^[0-9a-f]{16}$")


def read_kv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            raise ValueError(f"malformed_line:{path.name}:{line!r}")
        key, value = line.split("=", 1)
        if not key or key in result:
            raise ValueError(f"duplicate_or_empty_key:{path.name}:{key!r}")
        result[key] = value
    return result


def integer(data: dict[str, str], key: str, expected: int) -> None:
    try:
        actual = int(data[key], 10)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"invalid_integer:{key}") from exc
    if actual != expected:
        raise ValueError(f"count_mismatch:{key}:{actual}!={expected}")


def finite_nonnegative(data: dict[str, str], key: str) -> float:
    try:
        value = float(data[key])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"invalid_number:{key}") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid_finite_nonnegative:{key}")
    return value


def audit(frame_path: Path, reset_path: Path) -> dict[str, object]:
    frame = read_kv(frame_path)
    reset = read_kv(reset_path)
    integer(frame, "bench_requested_frames", 10_000)
    integer(frame, "bench_executed_frames", 10_000)
    integer(reset, "bench_resets", 100_000)
    frame_ms = finite_nonnegative(frame, "ms_per_frame")
    reset_us = finite_nonnegative(reset, "us_per_reset")
    finite_nonnegative(frame, "wall_seconds")
    finite_nonnegative(frame, "frames_per_second")
    finite_nonnegative(reset, "wall_seconds")
    finite_nonnegative(reset, "resets_per_second")
    state_hash = frame.get("state_hash", "")
    if not HASH_RE.fullmatch(state_hash):
        raise ValueError("invalid_state_hash")
    frame_budget_ms = frame_ms
    reset_budget_ms = reset_us / 1_000.0
    return {
        "schema": "opsworld-host-cpu-envelope-audit-v1",
        "frame_samples": 10_000,
        "reset_samples": 100_000,
        "frame_ms_per_sample": frame_budget_ms,
        "reset_ms_per_sample": reset_budget_ms,
        "frame_within_16_667ms": frame_budget_ms <= 16.667,
        "reset_within_16_667ms": reset_budget_ms <= 16.667,
        "state_hash": state_hash,
        "decision": (
            "PASS_CPU_INSTRUMENT_ENVELOPE_ONLY"
            if frame_budget_ms <= 16.667 and reset_budget_ms <= 16.667
            else "HOLD_CPU_INSTRUMENT_COST"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("frame_stdout", type=Path)
    parser.add_argument("reset_stdout", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.frame_stdout, args.reset_stdout)
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "STOP_CONSTRUCTION_OR_PROVENANCE", "error": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
