#!/usr/bin/env python3
"""Host-only, non-formal probe-dose construction sensitivity check."""
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

import runner

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
DOSES = (1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40)
TARGET = "gradual_capacity_loss"
NO_LOSS_CONTROLS = (
    "gradual_capacity_no_loss",
    "demand_drift_no_loss",
    "stable_no_loss",
)


def median(values):
    return statistics.median(values) if values else None


def summarize(fixture, units):
    dose_fixture = copy.deepcopy(fixture)
    dose_fixture["probe_units"] = units
    pairs = runner.build(dose_fixture)["pairs"]
    by_mechanism = {name: [] for name in fixture["mechanisms"]}
    for pair in pairs:
        by_mechanism[pair["probe"]["mechanism"]].append(pair)

    target_pairs = by_mechanism[TARGET]
    target_advances = [
        p["no_probe"]["loss_tick"] - p["probe"]["loss_tick"]
        for p in target_pairs
        if p["no_probe"]["loss_tick"] is not None
        and p["probe"]["loss_tick"] is not None
    ]
    eligible = (
        len(target_pairs) == len(fixture["loads"]) * fixture["episodes_per_cell"]
        and len(target_advances) == len(target_pairs)
        and all(p["no_probe"]["loss_tick"] > max(fixture["probe_ticks"])
                for p in target_pairs)
    )
    controls = {}
    for mechanism in NO_LOSS_CONTROLS:
        group = by_mechanism[mechanism]
        controls[mechanism] = {
            "pairs": len(group),
            "no_probe_losses": sum(p["no_probe"]["loss_tick"] is not None for p in group),
            "probe_losses": sum(p["probe"]["loss_tick"] is not None for p in group),
            "probe_created_losses": sum(
                p["probe"]["loss_tick"] is not None
                and p["no_probe"]["loss_tick"] is None for p in group
            ),
        }
    return {
        "probe_units": units,
        "target_pairs": len(target_pairs),
        "target_eligible": eligible,
        "target_pairs_with_both_losses": len(target_advances),
        "target_median_advance_ticks": median(target_advances),
        "target_probe_loss_ticks": [p["probe"]["loss_tick"] for p in target_pairs],
        "target_no_probe_loss_ticks": [p["no_probe"]["loss_tick"] for p in target_pairs],
        "no_loss_controls": controls,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: construction_dose_check.py OUTPUT.json")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture_bytes = FIXTURE.read_bytes()
    runner_bytes = (HERE / "runner.py").read_bytes()
    fixture = json.loads(fixture_bytes)
    report = {
        "schema": "recovery-sentinel-probe-dose-construction-v1",
        "scope": "host-only construction sensitivity; not formal candidate/audit evidence",
        "allocation": fixture["allocation"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "runner_sha256": hashlib.sha256(runner_bytes).hexdigest(),
        "doses_tested_units": list(DOSES),
        "results": [summarize(fixture, units) for units in DOSES],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "construction_check": "COMPLETE_NONFORMAL",
        "doses": len(DOSES),
        "fixture_sha256": report["fixture_sha256"],
        "runner_sha256": report["runner_sha256"],
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
