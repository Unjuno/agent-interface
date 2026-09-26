"""Independent audit of read-only ViZDoom shared-memory snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def audit(path: Path) -> dict:
    raw = json.loads(path.read_text())
    errors = []
    samples = raw.get("samples", [])
    if raw.get("setup") != "initialized":
        errors.append("game setup incomplete")
    if raw.get("shm_open_fd", -1) < 0 or raw.get("shm_errno") != 0:
        errors.append("read-only shm_open failed")
    if raw.get("shm_size", 0) < 2404240:
        errors.append("shared segment smaller than ViZDoom 1.3.0 segment")
    if len(samples) < 200:
        errors.append(f"insufficient samples: {len(samples)}")
    for i, row in enumerate(samples):
        if row.get("mono_after_ns", 0) < row.get("mono_before_ns", 0):
            errors.append(f"sample {i}: monotonic bracket reversed")
        if row.get("game_tic") != 4 or row.get("map_tic") != 1 or row.get("api_tic") != 1:
            errors.append(f"sample {i}: snapshot values differed from observed run")
    span = (samples[-1]["mono_after_ns"] - samples[0]["mono_before_ns"]) if samples else 0
    if span < 1_400_000_000:
        errors.append(f"observation span too short: {span}")
    decision = "PASS_CONSTRUCTION_ONLY_SHM_SNAPSHOT_STALE" if not errors else "FAIL_AUDIT"
    return {
        "schema": "shm-visibility-construction-audit-v1",
        "decision": decision,
        "formal_allocation": False,
        "limitations": [
            "read-only GAME_TIC/MAP_TIC values are shared-state snapshots, not a live clock",
            "the API read is diagnostic cross-check and may share the same stale source",
            "this experiment does not establish scorer phase or authorize formal collection",
        ],
        "sample_count": len(samples),
        "monotonic_observation_span_ns": span,
        "distinct_shm_game_tics": sorted({r["game_tic"] for r in samples}),
        "distinct_shm_map_tics": sorted({r["map_tic"] for r in samples}),
        "distinct_api_tics": sorted({r["api_tic"] for r in samples}),
        "errors": errors,
        "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = audit(args.raw)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
