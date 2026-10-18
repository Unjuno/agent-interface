#!/usr/bin/env python3
"""Construction prototype composing the frozen health and ammo guard."""
import json
from pathlib import Path

from observable_signal_guard_v2 import ObservableSignalGuard

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "RESULT.json"


def make_guard(signal_id, source, hard_minimum):
    spec = {
        "op": "observable_signal_guard", "guard_id": f"a02-{signal_id}",
        "source_sequence": source["sequence"], "signal_id": signal_id,
        "source_value": source["value"], "hard_minimum": hard_minimum,
        "max_source_age_ms": 30000, "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision", "on_unknown": "needs_decision",
    }
    return ObservableSignalGuard(spec, source, source["binding"])


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    source = fixture["source"]
    guards = {
        "health": make_guard("health", source["health"], fixture["health_hard_minimum"]),
        "ammo": make_guard("ammo", source["ammo"], fixture["ammo_hard_minimum"]),
    }
    rows = []
    for sample in fixture["samples"]:
        outcomes = {name: guard.evaluate(sample[name]) for name, guard in guards.items()}
        invalidated = any(outcome["requires_new_decision"] for outcome in outcomes.values())
        rows.append({"name": sample["name"], "outcomes": outcomes,
                     "would_request_new_decision": invalidated})
    expected_invalidations = {
        "positive_baseline": False, "minimum_positive_ammo": False,
        "zero_ammo": True, "unknown_ammo": True, "stale_ammo_sequence": True,
        "ammo_binding_mismatch": True, "health_below_floor": True,
    }
    observed = {row["name"]: row["would_request_new_decision"] for row in rows}
    result = {
        "format": "59-v39-dual-signal-construction-result-v1",
        "classification": "composed guard construction prototype; not integrated/live",
        "live_allocation_invocations": 0,
        "rows": rows,
        "all_expected_invalidations": observed == expected_invalidations,
        "cases": len(rows),
        "method_gate": "PASS_DUAL_SIGNAL_FAIL_CLOSED" if observed == expected_invalidations
                       else "FAIL_DUAL_SIGNAL_CONTRACT",
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "classification", "cases", "all_expected_invalidations", "method_gate")},
        sort_keys=True))


if __name__ == "__main__":
    main()
