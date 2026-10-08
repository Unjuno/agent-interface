"""Scenario replay of saved manual HUD samples; no controller or game calls."""
import json
from pathlib import Path
import sys


def analyze(fixture):
    samples = fixture["samples"]
    scenarios = []
    for critical in fixture["guard_scenarios"]["critical_health_minimum"]:
        for max_loss in fixture["guard_scenarios"]["maximum_health_loss"]:
            hard_minimum = max(critical, 100 - max_loss)
            crossing = next((row for row in samples
                             if row["health"] < hard_minimum), None)
            if crossing is None:
                timing = "NO_CROSSING_IN_SELECTED_SAMPLES"
                game_seconds = None
            elif crossing["game_seconds"] <= 56.2:
                timing = "SAMPLED_DURING_PENDING_INTERVAL"
                game_seconds = crossing["game_seconds"]
            elif crossing["game_seconds"] >= 56.4:
                timing = "SAMPLED_AT_OR_AFTER_RETURN_BOUNDARY"
                game_seconds = crossing["game_seconds"]
            else:
                timing = "BOUNDARY_CLASSIFICATION_GAP"
                game_seconds = crossing["game_seconds"]
            scenarios.append({
                "critical_health_minimum": critical,
                "maximum_health_loss": max_loss,
                "hard_minimum": hard_minimum,
                "first_observed_below": game_seconds,
                "health_at_sample": None if crossing is None else crossing["health"],
                "sample_phase": None if crossing is None else crossing["phase"],
                "timing": timing,
            })
    return {
        "schema": "map01-astra-v39-health-guard-scenario-result-v1",
        "source_sample_count": len(samples),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "ammo_guard_disposition": "NOT_REPLAYED_SPARSE_SELECTED_SAMPLES",
        "status": "PASS_SCENARIO_REPLAY_ONLY",
    }


def main():
    fixture = json.loads(Path(sys.argv[1]).read_text())
    result = analyze(fixture)
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "scenarios": result["scenario_count"]}))


if __name__ == "__main__":
    main()
