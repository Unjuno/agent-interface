#!/usr/bin/env python3
"""Independent audit of the Windows EMI/Performance Counter bracket."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = "RAPL_Package0_PKG"


def locate(raw: dict, side: str) -> dict:
    devices = raw.get(side)
    if not isinstance(devices, list):
        raise ValueError(f"{side}:not-list")
    for device in devices:
        if device.get("error"):
            continue
        for channel in device.get("channels", []):
            if channel.get("name") == TARGET or device.get("metered_hardware_name") == TARGET:
                return {"device": device, "channel": channel}
    raise ValueError(f"{side}:target-channel-missing")


def verify(raw: dict) -> dict:
    if raw.get("schema") != "issue7728-windows-energy-counter-a01-v1":
        raise ValueError("schema-mismatch")
    counter = raw.get("counter", {})
    if counter.get("instance", "").casefold() != TARGET.casefold():
        raise ValueError("counter-instance-mismatch")
    if counter.get("counter_type") != "NumberOfItems64":
        raise ValueError("counter-not-64-bit-raw-items")
    if int(counter.get("status", "-1"), 0) != 0:
        raise ValueError("counter-status-not-zero")
    if "<LOCAL_HOST>" not in counter.get("returned_path", ""):
        raise ValueError("host-path-not-sanitized")

    before = locate(raw, "emi_before")
    after = locate(raw, "emi_after")
    bdev, bch = before["device"], before["channel"]
    adev, ach = after["device"], after["channel"]
    if bdev.get("version") != adev.get("version"):
        raise ValueError("emi-version-changed")
    if bch.get("unit_code") != 0 or ach.get("unit_code") != 0:
        raise ValueError("emi-unit-not-picowatt-hours")
    if bch.get("unit") != "picowatt-hours" or ach.get("unit") != "picowatt-hours":
        raise ValueError("emi-unit-label-mismatch")
    if bch.get("name") != TARGET or ach.get("name") != TARGET:
        raise ValueError("emi-metered-domain-mismatch")
    if (bdev.get("metered_hardware_name") or TARGET) != (adev.get("metered_hardware_name") or TARGET):
        raise ValueError("emi-metered-hardware-changed")

    eb = int(bch["absolute_energy"])
    ea = int(ach["absolute_energy"])
    tb = int(bch["absolute_time_100ns"])
    ta = int(ach["absolute_time_100ns"])
    ec = int(counter["raw_value"])
    if ea < eb or ta <= tb:
        raise ValueError("emi-nonmonotone-or-reset")
    if not eb <= ec <= ea:
        raise ValueError("performance-counter-outside-emi-bracket")
    return {
        "status": "PASS_COUNTER_ORACLE_MATCH",
        "issue": 7728,
        "target_domain": TARGET,
        "unit": "picowatt-hours",
        "emi_energy_before": str(eb),
        "performance_counter_raw": str(ec),
        "emi_energy_after": str(ea),
        "emi_delta": str(ea - eb),
        "emi_time_delta_100ns": str(ta - tb),
        "counter_bracketed": True,
        "wrap_observed": False,
        "route_or_effect_claim": False,
    }


def mutation_controls(raw: dict) -> list[dict]:
    controls = []
    unit_mutant = json.loads(json.dumps(raw))
    locate(unit_mutant, "emi_before")["channel"]["unit_code"] = 7
    try:
        verify(unit_mutant)
        controls.append({"name": "unit-relabel", "rejected": False})
    except (ValueError, KeyError, IndexError):
        controls.append({"name": "unit-relabel", "rejected": True})

    missing_mutant = json.loads(json.dumps(raw))
    for side in ("emi_before", "emi_after"):
        for device in missing_mutant.get(side, []):
            device["channels"] = [ch for ch in device.get("channels", []) if ch.get("name") != TARGET]
            if device.get("metered_hardware_name") == TARGET:
                device["metered_hardware_name"] = "OTHER"
    try:
        verify(missing_mutant)
        controls.append({"name": "missing-domain-channel", "rejected": False})
    except (ValueError, KeyError, IndexError):
        controls.append({"name": "missing-domain-channel", "rejected": True})

    bracket_mutant = json.loads(json.dumps(raw))
    end_energy = int(locate(bracket_mutant, "emi_after")["channel"]["absolute_energy"])
    bracket_mutant["counter"]["raw_value"] = str(end_energy + 10**15)
    try:
        verify(bracket_mutant)
        controls.append({"name": "counter-outside-bracket", "rejected": False})
    except (ValueError, KeyError, IndexError):
        controls.append({"name": "counter-outside-bracket", "rejected": True})
    return controls


def main() -> int:
    raw = json.loads((HERE / "raw-preflight.json").read_text(encoding="utf-8-sig"))
    result = verify(raw)
    controls = mutation_controls(raw)
    result["negative_controls"] = controls
    result["negative_controls_passed"] = all(x["rejected"] for x in controls)
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["negative_controls_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
