#!/usr/bin/env python3
"""Emit a deterministic, horizon-blind rent-or-compile event ledger."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures.json"
RAW = HERE / "raw.jsonl"
ALLOCATION = "RENT-COMPILE-5870-T0-20261001-01"


def simulate(config, max_prefix):
    compiled = False
    premium = 0
    cost = 0
    rows = []
    for step in range(1, max_prefix + 1):
        acquire = (not compiled and config["qualified"] and
                   config["direct_unit"] > config["guarded_unit"] and
                   premium >= config["setup_cost"])
        if acquire:
            compiled = True
            cost += config["setup_cost"]
        if compiled:
            action = "GUARDED"
            unit_cost = config["guarded_unit"]
        else:
            action = "DIRECT"
            unit_cost = config["direct_unit"]
        cost += unit_cost
        if action == "DIRECT":
            premium += max(0, config["direct_unit"] - config["guarded_unit"])
        rows.append({
            "type": "use",
            "config_id": config["id"],
            "step": step,
            "qualified": config["qualified"],
            "action": "COMPILE_THEN_GUARDED" if acquire else action,
            "compile_charge": config["setup_cost"] if acquire else 0,
            "unit_charge": unit_cost,
            "cumulative_cost": cost,
            "observed_direct_premium": premium,
        })
    return rows


def raw_records(fixture, fixture_bytes):
    yield {
        "type": "header",
        "schema": "rent-compile-5870-raw-v1",
        "allocation": ALLOCATION,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "policy": fixture["policy"],
    }
    for config in fixture["configurations"]:
        yield from simulate(config, fixture["max_prefix"])


def main():
    if RAW.exists():
        raise SystemExit("raw output already exists; refusing overwrite")
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    rows = list(raw_records(fixture, fixture_bytes))
    RAW.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                                  for row in rows), encoding="utf-8", newline="\n")
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(rows),
                      "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
