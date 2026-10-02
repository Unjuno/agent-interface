"""One-shot deterministic Issue #5739 T0 candidate; finite authored tables only."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORLD_BYTES = (HERE / "world.json").read_bytes()
WORLD = json.loads(WORLD_BYTES)
OUT = HERE / "candidate_raw.json"
if OUT.exists():
    raise FileExistsError(OUT)

scenarios = {}
for name, spec in WORLD["scenarios"].items():
    attempts = []
    for arm in sorted(set(spec) - {"family", "screened_out"}):
        values = spec[arm]
        for index, variant in enumerate(WORLD["sealed_variants"]):
            attempts.append({
                "attempt_id": f"{name}:{arm}:{variant}",
                "scenario": name,
                "cohort": "sealed_confirmation",
                "arm": arm,
                "variant": variant,
                "success": values["success"][index],
                "forbidden": variant in values["forbidden"],
            })
    family = list(spec["family"])
    screened_out = list(spec["screened_out"])
    if any(row["forbidden"] for row in attempts):
        label = "HARD_SAFETY_STOP"
        global_claim = False
    elif len(family) > 1:
        label = "HOLD_MULTIPLE_COMPARISON_UNADJUSTED"
        global_claim = False
    elif screened_out:
        label = "SURVIVOR_VS_BASELINE_ONLY_NO_GLOBAL_OPTIMALITY"
        global_claim = False
    else:
        label = "SURVIVOR_VS_BASELINE_ONLY"
        global_claim = False
    scenarios[name] = {
        "attempts": attempts,
        "comparison_family": family,
        "screened_out": screened_out,
        "allowed_claim": label,
        "global_optimality_claim": global_claim,
    }

raw = {
    "schema": "issue-5739-t0-raw-v1",
    "world_sha256": hashlib.sha256(WORLD_BYTES).hexdigest(),
    "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "scenarios": scenarios,
    "scope": "authored finite deterministic claim-boundary fixtures only",
}
OUT.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "scenario_labels": {name: value["allowed_claim"] for name, value in scenarios.items()},
    "attempt_count": sum(len(value["attempts"]) for value in scenarios.values()),
    "global_optimality_claims": sum(value["global_optimality_claim"] for value in scenarios.values()),
    "scope": raw["scope"],
}, indent=2, sort_keys=True))
