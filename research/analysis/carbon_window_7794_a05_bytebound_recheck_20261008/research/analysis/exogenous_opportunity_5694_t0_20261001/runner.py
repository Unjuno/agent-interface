"""Deterministic no-model event traces for Issue #5694's synthetic T0."""
from __future__ import annotations

import json
from pathlib import Path


def build_raw() -> dict:
    opportunities = [
        {"id": "O1", "onset_ms": 0, "expiry_ms": 80, "region": "R1"},
        {"id": "O2", "onset_ms": 100, "expiry_ms": 180, "region": "R2"},
        {"id": "O3", "onset_ms": 200, "expiry_ms": 280, "region": "R3"},
    ]
    dense = {
        "cycles": [{"start_ms": 0, "end_ms": 30}, {"start_ms": 100, "end_ms": 130}, {"start_ms": 200, "end_ms": 230}],
        "effects": [
            {"id": "D1", "time_ms": 35, "regions": ["R1"]},
            {"id": "D2", "time_ms": 135, "regions": ["R2"]},
            {"id": "D3", "time_ms": 235, "regions": ["R3"]},
        ],
        "safe_stops": [],
        "busy_intervals": [],
    }
    sparse = {
        "cycles": [{"start_ms": 0, "end_ms": 5}, {"start_ms": 210, "end_ms": 215}],
        "effects": [
            {"id": "S1", "time_ms": 10, "regions": ["R1"]},
            {"id": "S2", "time_ms": 220, "regions": ["R3"]},
        ],
        "safe_stops": [],
        "busy_intervals": [{"start_ms": 5, "end_ms": 210}],
    }
    no_stall = {
        "cycles": [{"start_ms": 0, "end_ms": 5}, {"start_ms": 100, "end_ms": 105}, {"start_ms": 200, "end_ms": 205}],
        "effects": [
            {"id": "F1", "time_ms": 10, "regions": ["R1"]},
            {"id": "F2", "time_ms": 110, "regions": ["R2"]},
            {"id": "F3", "time_ms": 210, "regions": ["R3"]},
        ],
        "safe_stops": [],
        "busy_intervals": [],
    }
    safe_stop = {
        "cycles": [], "effects": [], "safe_stops": [{"time_ms": 50, "region": "R1"}],
        "busy_intervals": [],
    }
    idle = {"cycles": [], "effects": [], "safe_stops": [], "busy_intervals": []}
    overlap = {
        "cycles": [{"start_ms": 70, "end_ms": 75}],
        "effects": [
            {"id": "X1", "time_ms": 75, "regions": ["A-region", "B-region"]},
            {"id": "X2", "time_ms": 120, "regions": ["B-region"]},
        ],
        "safe_stops": [], "busy_intervals": [],
    }
    b_only = {
        "cycles": [{"start_ms": 70, "end_ms": 75}],
        "effects": [{"id": "X3", "time_ms": 75, "regions": ["B-region"]}],
        "safe_stops": [], "busy_intervals": [],
    }
    unsynced = {
        "cycles": [{"start_ms": 0, "end_ms": 5}],
        "effects": [{"id": "U-E1", "time_ms": 10, "regions": ["R1"]}],
        "safe_stops": [], "busy_intervals": [],
    }
    no_exogenous = {
        "cycles": [{"start_ms": 0, "end_ms": 5}],
        "effects": [], "safe_stops": [], "busy_intervals": [],
    }
    return {
        "schema": "exogenous-opportunity-5694-raw-v1",
        "scenarios": [
            {
                "name": "inversion", "horizon_ms": 320, "clock_aligned": True,
                "opportunities": opportunities, "arms": {"dense": dense, "sparse": sparse},
            },
            {
                "name": "no_stall", "horizon_ms": 320, "clock_aligned": True,
                "opportunities": opportunities, "arms": {"fast": no_stall, "dense": dense},
            },
            {
                "name": "safe_stop", "horizon_ms": 120, "clock_aligned": True,
                "opportunities": [{"id": "S1", "onset_ms": 0, "expiry_ms": 100, "region": "R1"}],
                "arms": {"guarded": safe_stop},
            },
            {
                "name": "expiry", "horizon_ms": 120, "clock_aligned": True,
                "opportunities": [{"id": "E1", "onset_ms": 0, "expiry_ms": 100, "region": "R1"}],
                "arms": {"idle": idle},
            },
            {
                "name": "censored", "horizon_ms": 50, "clock_aligned": True,
                "opportunities": [{"id": "C1", "onset_ms": 0, "expiry_ms": 100, "region": "R1"}],
                "arms": {"idle": idle},
            },
            {
                "name": "overlap", "horizon_ms": 160, "clock_aligned": True,
                "opportunities": [
                    {"id": "A", "onset_ms": 0, "expiry_ms": 100, "region": "A-region"},
                    {"id": "B", "onset_ms": 50, "expiry_ms": 150, "region": "B-region"},
                ],
                "arms": {"both": overlap, "b_only": b_only},
            },
            {
                "name": "unsynced", "horizon_ms": 120, "clock_aligned": False,
                "opportunities": [{"id": "U1", "onset_ms": 0, "expiry_ms": 100, "region": "R1"}],
                "arms": {"local": unsynced},
            },
            {
                "name": "no_exogenous", "horizon_ms": 100, "clock_aligned": True,
                "opportunities": [], "arms": {"idle": no_exogenous},
            },
        ],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    args = parser.parse_args()
    Path(args.raw).write_text(json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
