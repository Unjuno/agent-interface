#!/usr/bin/env python3
"""Exploratory T0 simulator for issue #7466; standard library only."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

N_SEEDS = 400
HORIZON = 80
CHECKPOINT_COST = 3.0
COHORTS = ("informative", "uninformative")
POLICIES = ("fixed", "event", "adaptive")


def one(seed: int, cohort: str, policy: str) -> dict[str, int | float | str]:
    rng = random.Random(seed)
    last_checkpoint = 0
    checkpoint_count = 0
    lost_work = 0
    failures = 0
    for tick in range(HORIZON):
        # Oracle-free runtime-visible schedule flag. In the informative cohort,
        # it perfectly identifies a four-tick high-risk window; the uninformative
        # cohort has a stationary hazard and no usable signal.
        signal = cohort == "informative" and tick % 20 in (8, 9, 10, 11)
        event_boundary = (tick + 1) % 5 == 0
        if policy == "fixed":
            checkpoint = (tick + 1) % 10 == 0
        elif policy == "event":
            checkpoint = event_boundary
        elif policy == "adaptive":
            # Cost proxy: visible conditional hazard times a fixed 16-tick
            # exposure estimate. With no signal, abstain to event boundaries.
            checkpoint = (signal and 0.25 * 16 > CHECKPOINT_COST) or (
                event_boundary and cohort == "uninformative"
            )
        else:
            raise ValueError(policy)

        # Interruptions affect the state before any checkpoint decision at this
        # tick. Draws are paired by seed across policies/cohorts.
        hazard = (0.25 if signal else 0.01) if cohort == "informative" else 0.05
        if rng.random() < hazard:
            failures += 1
            lost_work += tick - last_checkpoint
            last_checkpoint = tick
            checkpoint_count += 1  # recovery point after restart
        if checkpoint:
            checkpoint_count += 1
            last_checkpoint = tick + 1

    return {
        "seed": seed,
        "cohort": cohort,
        "policy": policy,
        "total_cost": lost_work + checkpoint_count * CHECKPOINT_COST,
        "lost_work": lost_work,
        "interruptions": failures,
        "checkpoints": checkpoint_count,
    }


def run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw.jsonl"
    rows = [one(seed, cohort, policy) for seed in range(N_SEEDS)
            for cohort in COHORTS for policy in POLICIES]
    raw_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                        encoding="utf-8")
    summary = {
        "n_seeds_per_cell": N_SEEDS,
        "horizon": HORIZON,
        "checkpoint_cost": CHECKPOINT_COST,
        "rows": len(rows),
        "cells": {
            f"{cohort}/{policy}": {
                "mean_total_cost": sum(float(r["total_cost"]) for r in rows
                                       if r["cohort"] == cohort and r["policy"] == policy) / N_SEEDS,
                "mean_lost_work": sum(int(r["lost_work"]) for r in rows
                                      if r["cohort"] == cohort and r["policy"] == policy) / N_SEEDS,
                "mean_checkpoints": sum(int(r["checkpoints"]) for r in rows
                                         if r["cohort"] == cohort and r["policy"] == policy) / N_SEEDS,
            }
            for cohort in COHORTS for policy in POLICIES
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
