#!/usr/bin/env python3
"""Host-only schedule/amplitude construction candidate; not a formal allocation."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "recovery_sentinel_5776_probe_intervention_t1_20261001_02"
AMPLITUDES = (1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40)
SCHEDULES = ((16,), (32,), (48,), (16, 32), (16, 48), (32, 48), (16, 32, 48))


def load_runner():
    spec = importlib.util.spec_from_file_location("frozen_probe_runner", SOURCE / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash(events):
    packed = json.dumps(events, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(packed).hexdigest()


def build():
    runner = load_runner()
    fixture_bytes = (SOURCE / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    cells = []
    for ticks in SCHEDULES:
        for units in AMPLITUDES:
            fx = dict(fixture, probe_ticks=list(ticks), probe_units=units)
            pairs = []
            for li, (load_name, demand) in enumerate(fx["loads"].items()):
                for mechanism in fx["mechanisms"]:
                    for eid in range(fx["episodes_per_cell"]):
                        arms = {}
                        for key, probed in (("probe", True), ("no_probe", False)):
                            arm = runner.simulate_arm(fx, li, demand, mechanism, eid, probed)
                            arms[key] = {
                                "loss_tick": arm["loss_tick"],
                                "backlog_area": arm["backlog_area"],
                                "probe_ticks_delivered": arm["probe_ticks_delivered"],
                                "probe_units_total": arm["probe_units_total"],
                                "event_sha256": event_hash(arm["events"]),
                            }
                        pairs.append({
                            "pair_id": f"{load_name}:{mechanism}:{eid:02d}",
                            "phase_tick": (eid * 11 + li * 3) % fx["horizon_ticks"],
                            **arms,
                        })
            cells.append({"probe_ticks": list(ticks), "probe_units": units, "pairs": pairs})
    return {
        "schema": "recovery-sentinel-probe-schedule-construction-raw-v1",
        "allocation": "construction-only-5776-schedule-amplitude-grid-20261001-01",
        "source_fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "grid": {"amplitudes": list(AMPLITUDES), "schedules": [list(x) for x in SCHEDULES]},
        "scope": "host-only deterministic construction; compact endpoints plus per-arm event commitments",
        "cells": cells,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py RAW.json")
    output = Path(sys.argv[1])
    if output.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    doc = build()
    encoded = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    print(json.dumps({"candidate": "EXIT_0_NONFORMAL", "cells": len(doc["cells"]),
                      "pairs": len(doc["cells"]) * 90, "arms": len(doc["cells"]) * 180,
                      "raw_sha256": hashlib.sha256(encoded).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
