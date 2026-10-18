"""Deterministic, offline age-vs-signal guard characterization."""
import json
from pathlib import Path

from source.observable_signal_guard_v2 import ObservableSignalGuard


ROOT = Path(__file__).parent


def evaluate(case, signal_id, source_value, current_value, hard_minimum,
             max_age_ms, age_ms):
    binding = {"surface": 1, "geometry": [0, 0, 640, 480]}
    source_ns = 1_000_000_000
    source = {"status": "observed", "signal_id": signal_id,
              "value": source_value, "sequence": 1,
              "capture_ns": source_ns, "binding": binding}
    spec = {"op": "observable_signal_guard",
            "guard_id": f"a14-{case['iteration']}-{signal_id}",
            "source_sequence": 1, "signal_id": signal_id,
            "source_value": source_value, "hard_minimum": hard_minimum,
            "max_source_age_ms": max_age_ms,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision",
            "on_unknown": "needs_decision"}
    guard = ObservableSignalGuard(spec, source, binding)

    def current(value):
        capture_ns = source_ns + round(age_ms * 1_000_000)
        return {"status": "observed", "signal_id": signal_id,
                "value": value, "sequence": 2,
                "capture_ns": capture_ns, "binding": binding}

    return guard.evaluate(current(current_value))


def run():
    inputs = json.loads((ROOT / "INPUTS.json").read_text(encoding="utf-8"))
    rows = []
    for case in inputs["cases"]:
        age = case["observed_age_ms"]
        age_cap = case["authored_max_source_age_ms"]
        actual_health = evaluate(case, "health", case["health_source"],
                                 case["health_current"],
                                 case["health_hard_minimum"], age_cap, age)
        actual_ammo = evaluate(case, "ammo", case["ammo_source"],
                               case["ammo_current"], case["ammo_hard_minimum"],
                               age_cap, age)
        isolated_health = evaluate(case, "health", case["health_source"],
                                   case["health_current"],
                                   case["health_hard_minimum"], 30000, age)
        isolated_ammo = evaluate(case, "ammo", case["ammo_source"],
                                 case["ammo_current"], case["ammo_hard_minimum"],
                                 30000, age)
        crossing_health = evaluate(case, "health", case["health_source"],
                                   case["health_hard_minimum"] - 1,
                                   case["health_hard_minimum"], 30000, age)
        expired_crossing_health = evaluate(
            case, "health", case["health_source"],
            case["health_hard_minimum"] - 1,
            case["health_hard_minimum"], age_cap, age)
        rows.append({
            "iteration": case["iteration"],
            "observed_age_ms": age,
            "authored_cap_ms": age_cap,
            "retained_outcomes": {
                "health": {"status": actual_health["status"],
                           "reason": actual_health["reason"]},
                "ammo": {"status": actual_ammo["status"],
                         "reason": actual_ammo["reason"]}},
            "same_samples_age_cap_30000ms": {
                "health": {"status": isolated_health["status"],
                           "reason": isolated_health["reason"]},
                "ammo": {"status": isolated_ammo["status"],
                         "reason": isolated_ammo["reason"]}},
            "health_below_hard_minimum_age_cap_30000ms": {
                "status": crossing_health["status"],
                "reason": crossing_health["reason"]},
            "health_below_hard_minimum_while_expired": {
                "status": expired_crossing_health["status"],
                "reason": expired_crossing_health["reason"],
                "requires_new_decision": expired_crossing_health["requires_new_decision"],
                "keep_existing_policy": expired_crossing_health["keep_existing_policy"]},
        })
    return {"format": "v39-age-guard-posthoc-result-v1",
            "classification": "OFFLINE_POSTHOC_CHARACTERIZATION",
            "cases": rows,
            "interpretation": "A14's two observed invalidations classify as source expiry before a hard health crossing. With the age cap raised solely for counterfactual isolation, same-sample health remains unchanged and ammo is soft-changed; an explicitly synthesized health value below the frozen hard minimum is hard-invalidated. When that below-floor value is paired with an expired age, status remains UNKNOWN/source_expired, but the guard still requires a new decision and does not keep the existing policy.",
            "limitations": [
                "The 30000 ms cap is a diagnostic counterfactual, not a live setting recommendation.",
                "The synthesized health crossing is not an observed A14 event.",
                "The expired-plus-below-floor combination is a synthetic guard input, not an observed A14 event.",
                "This establishes guard classification only, not monitor timing, enemy attribution, safe behavior, task effect, or live efficacy.",
                "A14 remains a protocol-deviation run and its raw record is untouched."]}


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
