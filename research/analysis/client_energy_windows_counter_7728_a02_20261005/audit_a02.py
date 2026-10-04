#!/usr/bin/env python3
"""Independent raw audit for the six-sample Windows EMI bracket."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = "RAPL_Package0_PKG"


def channel(devices: list[dict]) -> tuple[dict, dict]:
    for device in devices:
        if device.get("error"):
            continue
        for item in device.get("channels", []):
            if item.get("name", "").casefold() == TARGET.casefold():
                return device, item
    raise ValueError("target-channel-missing")


def verify(raw: dict) -> dict:
    if raw.get("schema") != "issue7728-windows-energy-counter-a02-v1":
        raise ValueError("schema-mismatch")
    energy = raw.get("energy_samples")
    cpu = raw.get("cpu_samples")
    if not isinstance(energy, list) or len(energy) != 6:
        raise ValueError("energy-sample-count-not-six")
    if not isinstance(cpu, list) or len(cpu) != 6:
        raise ValueError("cpu-sample-count-not-six")

    before_device, before = channel(raw.get("emi_before", []))
    after_device, after = channel(raw.get("emi_after", []))
    if before_device.get("version") != after_device.get("version") or before_device.get("version") != 2:
        raise ValueError("emi-v2-required")
    for item in (before, after):
        if item.get("unit_code") != 0 or item.get("unit") != "picowatt-hours":
            raise ValueError("emi-unit-not-picowatt-hours")
    eb, ea = int(before["absolute_energy"]), int(after["absolute_energy"])
    tb, ta = int(before["absolute_time_100ns"]), int(after["absolute_time_100ns"])
    if ea < eb or ta <= tb:
        raise ValueError("emi-nonmonotone-or-reset")

    previous_time = None
    previous_energy = None
    deltas = []
    for index, sample in enumerate(energy):
        if sample.get("instance", "").casefold() != TARGET.casefold():
            raise ValueError(f"energy-instance-mismatch-{index}")
        if int(sample.get("status", "-1"), 0) != 0:
            raise ValueError(f"energy-status-nonzero-{index}")
        if sample.get("counter_type") != "NumberOfItems64":
            raise ValueError(f"energy-not-raw-64-{index}")
        if "<LOCAL_HOST>" not in sample.get("returned_path", ""):
            raise ValueError(f"energy-host-not-sanitized-{index}")
        timestamp = sample.get("timestamp_utc", "")
        value = int(sample["raw_value"])
        if not eb <= value <= ea:
            raise ValueError(f"energy-outside-emi-bracket-{index}")
        if previous_time is not None and timestamp <= previous_time:
            raise ValueError("energy-timestamps-not-strictly-monotone")
        if previous_energy is not None:
            if value <= previous_energy:
                raise ValueError("energy-raw-not-strictly-monotone")
            deltas.append(value - previous_energy)
        previous_time, previous_energy = timestamp, value

    cpu_values = []
    for index, sample in enumerate(cpu):
        if int(sample.get("status", "-1"), 0) != 0:
            raise ValueError(f"cpu-status-nonzero-{index}")
        value = float(sample["cooked_value"])
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"cpu-value-out-of-range-{index}")
        cpu_values.append(value)
    if [x["timestamp_utc"] for x in cpu] != sorted(x["timestamp_utc"] for x in cpu):
        raise ValueError("cpu-timestamps-not-monotone")

    return {
        "status": "PASS_SIX_SAMPLE_COUNTER_ORACLE_MATCH",
        "issue": 7728,
        "target_domain": TARGET,
        "unit": "picowatt-hours",
        "counter_sample_count": len(energy),
        "energy_raw_first": str(int(energy[0]["raw_value"])),
        "energy_raw_last": str(int(energy[-1]["raw_value"])),
        "emi_energy_before": str(eb),
        "emi_energy_after": str(ea),
        "emi_energy_delta": str(ea - eb),
        "emi_time_delta_100ns": str(ta - tb),
        "counter_interval_min_delta": str(min(deltas)),
        "counter_interval_max_delta": str(max(deltas)),
        "distinct_counter_interval_deltas": len(set(deltas)),
        "cpu_samples": len(cpu_values),
        "cpu_mean_percent": round(sum(cpu_values) / len(cpu_values), 3),
        "cpu_min_percent": round(min(cpu_values), 3),
        "cpu_max_percent": round(max(cpu_values), 3),
        "counter_bracketed": True,
        "route_or_effect_claim": False,
    }


def mutation_controls(raw: dict) -> list[dict]:
    mutants = []
    wrong_unit = json.loads(json.dumps(raw))
    _, ch = channel(wrong_unit["emi_before"])
    ch["unit_code"] = 9
    mutants.append(("wrong-unit", wrong_unit))

    outside = json.loads(json.dumps(raw))
    _, ch = channel(outside["emi_after"])
    outside["energy_samples"][2]["raw_value"] = str(int(ch["absolute_energy"]) + 10**12)
    mutants.append(("out-of-bracket-sample", outside))

    dropped = json.loads(json.dumps(raw))
    dropped["energy_samples"].pop()
    mutants.append(("dropped-energy-sample", dropped))

    controls = []
    for name, mutant in mutants:
        try:
            verify(mutant)
            controls.append({"name": name, "rejected": False})
        except (ValueError, KeyError, TypeError, IndexError):
            controls.append({"name": name, "rejected": True})
    return controls


def main() -> int:
    raw = json.loads((HERE / "raw-a02.json").read_text(encoding="utf-8-sig"))
    result = verify(raw)
    result["negative_controls"] = mutation_controls(raw)
    result["negative_controls_passed"] = all(item["rejected"] for item in result["negative_controls"])
    (HERE / "audit-a02.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["negative_controls_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
