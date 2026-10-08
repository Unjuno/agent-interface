"""Build Stage-0 schedule-contract fixtures; this module never imports a model."""
from __future__ import annotations

import hashlib
import json


ALLOCATION = "needle-role-router-online-lora-audit-v2-20260928-stage0"
SCHEMA = "needle-role-router-stage0-fixture-v1"
FIXTURE_SEEDS = (17, 29, 43)  # Synthetic contract fixtures; not training seeds.
ARMS = (
    "SHARED_B_ONLY",
    "SHARED_A_REPLAY",
    "ROUTED_SHARED_ADAPTER",
    "ROUTED_SEPARATE_SKILLS",
)


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def base_schedule(seed: int) -> list[int]:
    """A deterministic 400-step index schedule, with no optimizer execution."""
    return [(seed * 17 + index * 37 + index // 7) % 256 for index in range(400)]


def arm_schedule(seed: int, arm: str) -> list[list[int]]:
    """Describe each arm's 16x8 arrivals without comparing unlike batches."""
    rows = []
    for arrival in range(16):
        for step in range(8):
            support_index = (seed + arrival * 13) % 16
            if arm == "SHARED_A_REPLAY":
                memory_index = (seed + arrival * 8 + step) % 16
                rows.append([support_index, memory_index])
            else:
                rows.append([support_index])
    return rows


def build_fixture() -> bytes:
    runs = []
    for seed in FIXTURE_SEEDS:
        schedule = base_schedule(seed)
        dataset = {"base_row_indices": schedule}
        arm_rows = []
        for arm in ARMS:
            updates = arm_schedule(seed, arm)
            arm_rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "update_count": len(updates),
                    "batch_row_indices": updates,
                    "schedule_sha256": digest(updates),
                }
            )
        runs.append(
            {
                "seed": seed,
                "base_row_indices": schedule,
                "dataset_sha256": {
                    key: digest(value) for key, value in dataset.items()
                },
                "arms": arm_rows,
            }
        )
    raw = {
        "schema": SCHEMA,
        "allocation": ALLOCATION,
        "fixture_seeds": list(FIXTURE_SEEDS),
        "arms": list(ARMS),
        "fit_invocations": 0,
        "optimizer_updates": 0,
        "runs": runs,
    }
    return canonical(raw) + b"\n"


if __name__ == "__main__":
    import argparse
    import hashlib
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_fixture()
    if args.output:
        from pathlib import Path

        with Path(args.output).open("xb") as output:
            output.write(payload)
        print(json.dumps({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}))
    else:
        sys.stdout.buffer.write(payload)
