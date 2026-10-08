#!/usr/bin/env python3
"""Single deterministic probe of current-main v39 cover guard semantics."""
import json
from pathlib import Path

from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "fixture.json"
OUTPUT = ROOT / "RESULT.json"


class HealthReader:
    def read(self, observation):
        return observation["health"]


def main():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture = json.loads(INPUT.read_text(encoding="utf-8"))
    source = fixture["source"]
    spec = {
        "op": "observable_signal_guard",
        "guard_id": "a01-health-cover",
        "source_sequence": source["sequence"],
        "signal_id": "health",
        "source_value": source["health"]["value"],
        "hard_minimum": fixture["authored_health_hard_minimum"],
        "max_source_age_ms": 30000,
        "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision",
        "on_unknown": "needs_decision",
    }
    guard = ObservableSignalGuard(spec, source["health"], source["health"]["binding"])
    monitor = ObservableSignalPolicyMonitor(guard, HealthReader())
    observations = []
    for sample in fixture["samples"]:
        binding = source["health"]["binding"]
        observation = {
            "sequence": sample["sequence"],
            "health": {"format": "observable-signal-v1", "signal_id": "health",
                       "status": "observed", "value": sample["health"],
                       "sequence": sample["sequence"], "capture_ns": sample["capture_ns"],
                       "binding": binding},
            "ammo": {"format": "observable-signal-v1", "signal_id": "ammo",
                     "status": "observed", "value": sample["ammo"],
                     "sequence": sample["sequence"], "capture_ns": sample["capture_ns"],
                     "binding": binding},
        }
        event = monitor.observe(observation)
        observations.append({"name": sample["name"], "health": sample["health"],
                             "ammo": sample["ammo"],
                             "monitor_event": None if event is None else event["outcome"],
                             "would_request_new_decision": bool(
                                 event and event["outcome"]["requires_new_decision"]),
                             "cover_commands": fixture["notional_active_cover"]})
    result = {
        "format": "59-v39-ammo-cover-guard-result-v1",
        "classification": "synthetic current-source boundary probe; not live behavior",
        "formal_live_allocation_invocations": 0,
        "guard_signal_id": spec["signal_id"],
        "observations": observations,
        "ammo_depletion_invalidated": observations[1]["would_request_new_decision"],
        "unchanged_positive_ammo_preserved": not observations[0]["would_request_new_decision"],
        "health_hard_floor_invalidated": observations[2]["would_request_new_decision"],
        "method_gate": "PASS" if (
            observations[1]["would_request_new_decision"] and
            not observations[0]["would_request_new_decision"] and
            observations[2]["would_request_new_decision"]
        ) else "FAIL_AMMO_DEPLETION_NOT_GUARDED",
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "classification", "ammo_depletion_invalidated",
        "unchanged_positive_ammo_preserved", "health_hard_floor_invalidated", "method_gate")},
        sort_keys=True))


if __name__ == "__main__":
    main()
