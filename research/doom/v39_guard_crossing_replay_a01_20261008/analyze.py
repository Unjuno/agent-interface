"""Conditional guard-crossing analysis over retained MAP01 HUD readouts."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "map01_astra_wait_hud_dense_replay_59_a01_20261005" / "VISUAL_READOUT.json"
OUT = ROOT / "RESULT.json"
EXPECTED_SOURCE_SHA256 = "610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724"


def main():
    source_bytes = SOURCE.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"source digest mismatch: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}")
    readout = json.loads(source_bytes)
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
    by_first = {}
    for p in policies:
        first = p["first_invalidating_sample"]
        key = "never_during_wait" if first is None else str(first["game_seconds"])
        by_first[key] = by_first.get(key, 0) + 1
    by_first.setdefault("never_during_wait", 0)
    # Independent oracle groups parameter pairs by floor, then counts each
    # floor only when the running minimum health first crosses it.
    floor_counts = {}
    for c in range(1, min(h0, 200) + 1):
        for loss in range(21):
            floor = max(c, h0 - loss)
            floor_counts[floor] = floor_counts.get(floor, 0) + 1
    oracle_by_first = {}
    previous_minimum = h0
    for sample in wait:
        health = sample["health"]
        crossing_count = sum(
            count for floor, count in floor_counts.items()
            if health < floor <= previous_minimum)
        if crossing_count:
            key = str(float(sample["game_clock"].removesuffix("s")))
            oracle_by_first[key] = oracle_by_first.get(key, 0) + crossing_count
        previous_minimum = min(previous_minimum, health)
    oracle_by_first["never_during_wait"] = sum(
        count for floor, count in floor_counts.items() if floor <= previous_minimum)
    if len(policies) != 2100 or sum(oracle_by_first.values()) != 2100:
        raise ValueError(f"unexpected policy count: {len(policies)}")
    if by_first != oracle_by_first:
        raise ValueError(
            f"enumeration/oracle mismatch: {by_first!r} != {oracle_by_first!r}")
    never_count = by_first["never_during_wait"]
    later_count = sum(count for key, count in by_first.items()
                      if key not in ("47.0", "never_during_wait"))
    result = {
        "schema": "map01-v39-guard-crossing-retained-replay-a01-v1",
        "status": "PASS_CONDITIONAL_FINITE_ENUMERATION",
        "scope": "Posthoc application of current-main V39 health guard contract to one prior run's manual HUD readouts; no deployment or live efficacy claim.",
        "source": "research/doom/map01_astra_wait_hud_dense_replay_59_a01_20261005/VISUAL_READOUT.json",
        "source_sha256": source_sha256,
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
            "policies_invalidating_on_first_damage_sample_47_0": by_first.get("47.0", 0),
            "policies_invalidating_later_during_wait": later_count,
            "policies_never_invalidating_during_wait": never_count,
            "first_sample_distribution": by_first,
            "independent_threshold_oracle": {
                "first_sample_distribution": oracle_by_first
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
