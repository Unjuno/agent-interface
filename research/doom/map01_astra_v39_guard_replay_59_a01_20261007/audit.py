"""Independent raw-only recomputation of the frozen guard scenarios."""
import json
from pathlib import Path
import sys


def audit(fixture, observed):
    errors = []
    samples = fixture.get("samples")
    if type(samples) is not list or len(samples) != 10:
        return ["SAMPLE_DENOMINATOR"]
    clocks = [row.get("game_seconds") for row in samples]
    if clocks != sorted(set(clocks)):
        errors.append("SAMPLE_ORDER")
    for row in samples:
        if (type(row.get("health")) is not int or
                type(row.get("ammo")) is not int or
                len(row.get("image_sha256", "")) != 64):
            errors.append("SAMPLE_SCHEMA")
    expected = []
    for critical in fixture["guard_scenarios"]["critical_health_minimum"]:
        for max_loss in fixture["guard_scenarios"]["maximum_health_loss"]:
            floor = max(critical, 100 - max_loss)
            below = [row for row in samples if row["health"] < floor]
            first = below[0] if below else None
            expected.append({
                "critical_health_minimum": critical,
                "maximum_health_loss": max_loss,
                "hard_minimum": floor,
                "first_observed_below": None if first is None else first["game_seconds"],
                "health_at_sample": None if first is None else first["health"],
                "sample_phase": None if first is None else first["phase"],
                "timing": ("NO_CROSSING_IN_SELECTED_SAMPLES" if first is None else
                           "SAMPLED_DURING_PENDING_INTERVAL" if first["game_seconds"] <= 56.2 else
                           "SAMPLED_AT_OR_AFTER_RETURN_BOUNDARY" if first["game_seconds"] >= 56.4 else
                           "BOUNDARY_CLASSIFICATION_GAP"),
            })
    if observed.get("schema") != "map01-astra-v39-health-guard-scenario-result-v1":
        errors.append("RESULT_SCHEMA")
    if observed.get("source_sample_count") != len(samples):
        errors.append("SOURCE_COUNT")
    if observed.get("scenario_count") != len(expected):
        errors.append("SCENARIO_COUNT")
    if observed.get("scenarios") != expected:
        errors.append("SCENARIO_RECOMPUTATION")
    if observed.get("ammo_guard_disposition") != "NOT_REPLAYED_SPARSE_SELECTED_SAMPLES":
        errors.append("AMMO_SCOPE")
    return errors


def main():
    fixture = json.loads(Path(sys.argv[1]).read_text())
    result = json.loads(Path(sys.argv[2]).read_text())
    errors = audit(fixture, result)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors,
                      "scenarios": result.get("scenario_count")}))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
