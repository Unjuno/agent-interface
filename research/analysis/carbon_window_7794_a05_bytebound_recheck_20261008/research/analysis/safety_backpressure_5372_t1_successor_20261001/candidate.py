#!/usr/bin/env python3
"""Allocation-02 envelope over the frozen T1 simulator source."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ALLOCATION = "SAFETY-BACKPRESSURE-ENDOGENOUS-DEMAND-5372-T1-20261001-02"
HERE = Path(__file__).resolve().parent
DEFAULT_SIMULATOR = HERE.parent / "safety_backpressure_5372_t1_v1" / "simulate.py"


def all_records(simulator_path: Path = DEFAULT_SIMULATOR) -> list[dict]:
    spec = importlib.util.spec_from_file_location("frozen_t1_simulator", simulator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen simulator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ALLOCATION = ALLOCATION
    return module.all_records()


def main() -> None:
    simulator_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SIMULATOR
    for record in all_records(simulator_path):
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
