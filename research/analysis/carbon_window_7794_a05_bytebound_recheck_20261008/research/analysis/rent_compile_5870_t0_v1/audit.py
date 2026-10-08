#!/usr/bin/env python3
"""Independent event-ledger and exact-prefix-regret auditor."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures.json"
RAW = HERE / "raw.jsonl"
OUT = HERE / "audit.json"
ALLOCATION = "RENT-COMPILE-5870-T0-20261001-01"
USE_KEYS = {"type", "config_id", "step", "qualified", "action", "compile_charge",
            "unit_charge", "cumulative_cost", "observed_direct_premium"}


def expected_rows(config, bound):
    is_compiled = False
    premium = 0
    paid = 0
    for step in range(1, bound + 1):
        buy_now = (not is_compiled and config["qualified"] and
                   config["direct_unit"] > config["guarded_unit"] and
                   premium >= config["setup_cost"])
        compile_charge = config["setup_cost"] if buy_now else 0
        if buy_now:
            is_compiled = True
        unit = config["guarded_unit"] if is_compiled else config["direct_unit"]
        action = "COMPILE_THEN_GUARDED" if buy_now else ("GUARDED" if is_compiled else "DIRECT")
        paid += compile_charge + unit
        if not is_compiled:
            premium += max(0, config["direct_unit"] - config["guarded_unit"])
        yield {"type": "use", "config_id": config["id"], "step": step,
               "qualified": config["qualified"], "action": action,
               "compile_charge": compile_charge, "unit_charge": unit,
               "cumulative_cost": paid, "observed_direct_premium": premium}


def parse(raw_bytes):
    return [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]


def evaluate(fixture, fixture_bytes, rows):
    errors = []
    if not rows or rows[0] != {"type": "header", "schema": "rent-compile-5870-raw-v1",
                               "allocation": ALLOCATION,
                               "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                               "policy": fixture["policy"]}:
        errors.append("header_or_fixture_identity")
        return {"errors": errors}
    offset = 1
    metrics = []
    expected_total = 1 + len(fixture["configurations"]) * fixture["max_prefix"]
    if len(rows) != expected_total:
        errors.append("row_count")
    for config in fixture["configurations"]:
        expected = list(expected_rows(config, fixture["max_prefix"]))
        actual = rows[offset:offset + fixture["max_prefix"]]
        offset += fixture["max_prefix"]
        if actual != expected:
            errors.append(config["id"] + ":candidate_event_ledger_mismatch")
        rent_regrets = []
        direct_regrets = []
        immediate_regrets = []
        for n in range(1, fixture["max_prefix"] + 1):
            online = expected[n - 1]["cumulative_cost"]
            direct = n * config["direct_unit"]
            immediate = config["setup_cost"] + n * config["guarded_unit"]
            offline = min(direct, immediate)
            rent_regrets.append(online - offline)
            direct_regrets.append(direct - offline)
            immediate_regrets.append(immediate - offline)
        eligible = config["qualified"] and config["direct_unit"] > config["guarded_unit"]
        metrics.append({
            "config_id": config["id"],
            "eligible_positive_saving": eligible,
            "rent_worst_prefix_regret": max(rent_regrets),
            "direct_worst_prefix_regret": max(direct_regrets),
            "compile_immediately_worst_prefix_regret": max(immediate_regrets),
            "rent_strictly_beats_direct": max(rent_regrets) < max(direct_regrets),
            "rent_strictly_beats_compile_immediately": max(rent_regrets) < max(immediate_regrets),
        })
    if rows[1:] and any(set(row) != USE_KEYS for row in rows[1:]):
        errors.append("unexpected_or_missing_fields")
    selected = [x for x in metrics if x["eligible_positive_saving"]]
    supports = all(x["rent_strictly_beats_direct"] and
                   x["rent_strictly_beats_compile_immediately"] for x in selected)
    return {"errors": errors, "metrics": metrics,
            "eligible_configurations": len(selected),
            "strict_improvement_hypothesis_supported": supports,
            "status": "SUPPORT_PURE_CASE_SCOPED" if not errors and supports
                      else "FAIL_ONLINE_VALUE_PURE_CASE" if not errors
                      else "STOP_AUDIT_OR_SOURCE_DRIFT"}


def audit(fixture, fixture_bytes, rows):
    controls = {}
    mutants = {}
    omitted = copy.deepcopy(rows)
    omitted.pop(2)
    mutants["omitted_event"] = omitted
    tampered = copy.deepcopy(rows)
    tampered[1]["unit_charge"] += 1
    mutants["false_unit_cost"] = tampered
    unqualified = copy.deepcopy(rows)
    index = 1 + 5 * fixture["max_prefix"]
    unqualified[index]["action"] = "COMPILE_THEN_GUARDED"
    mutants["compile_without_qualification"] = unqualified
    future_leak = copy.deepcopy(rows)
    future_leak[1]["known_horizon"] = fixture["max_prefix"]
    mutants["future_horizon_field"] = future_leak
    for name, changed in mutants.items():
        controls[name] = bool(evaluate(fixture, fixture_bytes, changed)["errors"])
    result = evaluate(fixture, fixture_bytes, rows)
    result["corruption_controls"] = controls
    result["corruption_controls_rejected"] = sum(controls.values())
    result["corruption_controls_total"] = len(controls)
    if not all(controls.values()) and not result["errors"]:
        result["status"] = "STOP_AUDIT_OR_SOURCE_DRIFT"
        result["errors"].append("corruption_control_false_accept")
    return result


def main():
    if OUT.exists():
        raise SystemExit("audit output already exists; refusing overwrite")
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    rows = parse(raw_path.read_bytes())
    result = audit(fixture, fixture_bytes, rows)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": len(result["errors"]),
                      "configs": len(result.get("metrics", [])),
                      "controls_rejected": result["corruption_controls_rejected"]},
                     sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
