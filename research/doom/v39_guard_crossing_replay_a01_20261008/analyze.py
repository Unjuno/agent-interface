"""Conditional guard-crossing analysis over retained MAP01 HUD readouts."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "map01_astra_wait_hud_dense_replay_59_a01_20261005" / "VISUAL_READOUT.json"
OUT = ROOT / "RESULT.json"


def main():
    readout = json.loads(SOURCE.read_text(encoding="utf-8"))
    samples = readout["samples"]
    wait = [s for s in samples if s["phase"] == "MODEL THINKING + LOCAL COVER"]
    h0 = wait[0]["health"]
    policies = []
    for c in range(1, min(h0, 200) + 1):
        for loss in range(0, 21):
            floor = max(c, h0 - loss)
            hits = [s for s in wait if s["health"] < floor]
            policies.append({"critical_minimum": c, "maximum_loss": loss,
                             "hard_minimum": floor,
                             "first_invalidating_sample": None if not hits else {
                                 "game_seconds": float(hits[0]["game_clock"].removesuffix("s")),
                                 "health": hits[0]["health"]}})
    count_wait = sum(p["first_invalidating_sample"] is not None for p in policies)
    by_first = {}
    for p in policies:
        first = p["first_invalidating_sample"]
        key = "never_during_wait" if first is None else str(first["game_seconds"])
        by_first[key] = by_first.get(key, 0) + 1
    # Independent closed-form oracle: floor >= 97 trips at health 96;
    # floor >= 95 but <97 first trips at 94; lower floors do not trip in-wait.
    first_damage_count = sum(max(c, h0 - loss) >= 97
                             for c in range(1, min(h0, 200) + 1)
                             for loss in range(21))
    later_count = sum(95 <= max(c, h0 - loss) < 97
                      for c in range(1, min(h0, 200) + 1)
                      for loss in range(21))
    never_count = sum(max(c, h0 - loss) < 95
                      for c in range(1, min(h0, 200) + 1)
                      for loss in range(21))
    assert (len(policies), first_damage_count, later_count, never_count) == (2100, 468, 222, 1410)
    result = {
        "schema": "map01-v39-guard-crossing-retained-replay-a01-v1",
        "status": "PASS_CONDITIONAL_FINITE_ENUMERATION",
        "scope": "Posthoc application of current-main V39 health guard contract to one prior run's manual HUD readouts; no deployment or live efficacy claim.",
        "source": "research/doom/map01_astra_wait_hud_dense_replay_59_a01_20261005/VISUAL_READOUT.json",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "assumptions": {
            "source_health": h0,
            "valid_critical_minimum": "integer 1..min(source_health, 200)",
            "valid_maximum_health_loss": "integer 0..20",
            "invalidation_rule": "current_health < max(critical_minimum, source_health - maximum_health_loss)",
            "ammo_rule": "for a fire cover, current ammo < 1 invalidates; this replay's sampled ammo stays >=37",
            "freshness_binding_and_same_epoch": "assumed valid in this posthoc value-only comparison; historical readout does not preserve V39 signal receipts"
        },
        "enumeration": {
            "policy_count": len(policies),
            "policies_invalidating_on_first_damage_sample_47_0": sum(p["first_invalidating_sample"] is not None and p["first_invalidating_sample"]["game_seconds"] == 47.0 for p in policies),
            "policies_invalidating_later_during_wait": sum(p["first_invalidating_sample"] is not None and p["first_invalidating_sample"]["game_seconds"] > 47.0 for p in policies),
            "policies_never_invalidating_during_wait": len(policies) - count_wait,
            "first_sample_distribution": by_first,
            "independent_closed_form_oracle": {
                "health_floor_at_least_97_first_trips_at_47_0_count": first_damage_count,
                "health_floor_95_or_96_first_trips_at_54_8_count": later_count,
                "health_floor_below_95_never_trips_in_wait_count": never_count
            }
        },
        "observations": [{"game_seconds": float(s["game_clock"].removesuffix("s")),
                          "health": s["health"], "ammo": s["ammo"], "phase": s["phase"]}
                         for s in wait + [s for s in samples if s["phase"] == "LOCAL PLAN / FEEDBACK"]],
        "interpretation": [
            "The fixed floor can invalidate only after the observed health falls below it; it cannot react to threat appearance while health and ammo remain unchanged.",
            "Health first visibly reads 96 at 47.0 seconds; this can invalidate only policies with hard_minimum >= 97, conditional on fresh correctly bound observations and monitor sampling.",
            "At 56.2 seconds health reads 94 during wait, but 87 is first sampled after return at 56.4; do not attribute that loss to wait-only policy behavior.",
            "Counts enumerate allowed parameter combinations, not recommended policy choices or observed V39 runtime behavior."
        ],
        "residual_empirical_questions": [
            "Whether current V39 observes changes at sufficient cadence during actual model waits.",
            "Whether a triggered invalidation cancels and physically releases each held key before answer return.",
            "Whether independently useful feedback, bounded recovery and the next action improve ammo/progress/terminal outcome under fresh live threat exposure."
        ]
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["enumeration"], indent=2))


if __name__ == "__main__":
    main()
