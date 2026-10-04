import json
from pathlib import Path

from observable_signal_guard_v2 import ObservableSignalGuard
from paired_guard import evaluate_pair

ROOT = Path(__file__).resolve().parent


def build_guard(signal_id, signal, floor):
    spec = {
        "op": "observable_signal_guard",
        "guard_id": "a03-" + signal_id,
        "source_sequence": signal["sequence"],
        "signal_id": signal_id,
        "source_value": signal["value"],
        "hard_minimum": floor,
        "max_source_age_ms": 30000,
        "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision",
        "on_unknown": "needs_decision",
    }
    return ObservableSignalGuard(spec, signal, signal["binding"])


def run(fixture):
    source = fixture["source"]
    health_guard = build_guard("health", source["health"], fixture["health_floor"])
    ammo_guard = build_guard("ammo", source["ammo"], fixture["ammo_floor"])
    rows = []
    for sample in fixture["samples"]:
        outcome = evaluate_pair(health_guard, ammo_guard, sample["health"], sample["ammo"])
        rows.append({
            "name": sample["name"],
            "expected": sample["expected"],
            "outcome": outcome,
        })
    return {
        "format": "59-v39-paired-health-ammo-result-v1",
        "classification": "synthetic paired-frame construction; not runtime-integrated or live",
        "live_allocation_invocations": 0,
        "rows": rows,
        "all_expected_decisions": all(
            row["outcome"]["requires_new_decision"] == row["expected"] for row in rows
        ),
    }


if __name__ == "__main__":
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = run(fixture)
    (ROOT / "RESULT.json").write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"cases": len(result["rows"]), "all_expected_decisions": result["all_expected_decisions"]}, sort_keys=True))
