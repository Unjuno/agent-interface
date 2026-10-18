#!/usr/bin/env python3
"""Probe paired-epoch gating before composing health/ammo policy guards."""
import json
from pathlib import Path

from observable_signal_guard_v2 import ObservableSignalGuard

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "RESULT.json"


def pair_valid(health, ammo):
    if type(health) is not dict or type(ammo) is not dict:
        return False, "not_objects"
    if health.get("status") != "observed" or ammo.get("status") != "observed":
        return False, "signal_unavailable"
    if health.get("signal_id") != "health" or ammo.get("signal_id") != "ammo":
        return False, "signal_identity_mismatch"
    for item in (health, ammo):
        if (type(item.get("sequence")) is not int or
                type(item.get("capture_ns")) is not int or
                type(item.get("binding")) is not dict or not item["binding"]):
            return False, "invalid_epoch_types"
    if health["sequence"] != ammo["sequence"]:
        return False, "sequence_mismatch"
    if health["capture_ns"] != ammo["capture_ns"]:
        return False, "capture_time_mismatch"
    if health["binding"] != ammo["binding"]:
        return False, "binding_mismatch"
    return True, "coherent_pair"


def make_guard(signal_id, source, floor, max_age):
    spec = {"op": "observable_signal_guard", "guard_id": f"a03-{signal_id}",
            "source_sequence": source["sequence"], "signal_id": signal_id,
            "source_value": source["value"], "hard_minimum": floor,
            "max_source_age_ms": max_age, "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}
    return ObservableSignalGuard(spec, source, source["binding"])


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    source = fixture["source"]
    guards = {
        "health": make_guard("health", source["health"],
                              fixture["health_hard_minimum"], fixture["max_source_age_ms"]),
        "ammo": make_guard("ammo", source["ammo"],
                           fixture["ammo_hard_minimum"], fixture["max_source_age_ms"]),
    }
    rows = []
    for case in fixture["cases"]:
        coherent, reason = pair_valid(case["health"], case["ammo"])
        outcomes = ({key: guard.evaluate(case[key]) for key, guard in guards.items()}
                    if coherent else {})
        invalidated = not coherent or any(x["requires_new_decision"] for x in outcomes.values())
        rows.append({"name": case["name"], "pair_coherent": coherent,
                     "pair_reason": reason, "outcomes": outcomes,
                     "would_request_new_decision": invalidated})
    expected = {"coherent_positive": False, "coherent_minimum_positive": False,
                "coherent_zero_ammo": True, "coherent_health_hard_floor": True,
                "sequence_mismatch": True, "capture_time_mismatch": True,
                "binding_mismatch": True, "boolean_sequence_alias": True,
                "float_sequence_alias": True, "unknown_ammo": True}
    actual = {row["name"]: row["would_request_new_decision"] for row in rows}
    result = {"format": "59-v39-paired-ammo-cover-result-v1",
              "classification": "paired-epoch construction prototype; not integrated/live",
              "live_allocation_invocations": 0, "rows": rows, "cases": len(rows),
              "all_expected_decisions": actual == expected,
              "method_gate": "PASS_PAIRED_EPOCH_FAIL_CLOSED" if actual == expected
                             else "FAIL_PAIRED_EPOCH_CONTRACT"}
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "classification", "cases", "all_expected_decisions", "method_gate")}, sort_keys=True))


if __name__ == "__main__":
    main()
