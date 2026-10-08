"""Independent raw-only auditor for Issue #5739 T0; does not import runner.py."""
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORLD_BYTES = (HERE / "world.json").read_bytes()
WORLD = json.loads(WORLD_BYTES)
RAW_BYTES = (HERE / "candidate_raw.json").read_bytes()
RAW = json.loads(RAW_BYTES)


def expected_scenario(name, spec):
    rows = []
    for arm in sorted(set(spec) - {"family", "screened_out"}):
        values = spec[arm]
        for index, variant in enumerate(WORLD["sealed_variants"]):
            rows.append({
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
    if any(row["forbidden"] for row in rows):
        label = "HARD_SAFETY_STOP"
    elif len(family) > 1:
        label = "HOLD_MULTIPLE_COMPARISON_UNADJUSTED"
    elif screened_out:
        label = "SURVIVOR_VS_BASELINE_ONLY_NO_GLOBAL_OPTIMALITY"
    else:
        label = "SURVIVOR_VS_BASELINE_ONLY"
    return {
        "attempts": rows,
        "comparison_family": family,
        "screened_out": screened_out,
        "allowed_claim": label,
        "global_optimality_claim": False,
    }


def validate(raw):
    if raw.get("schema") != "issue-5739-t0-raw-v1":
        return False
    if raw.get("world_sha256") != hashlib.sha256(WORLD_BYTES).hexdigest():
        return False
    if raw.get("runner_sha256") != hashlib.sha256((HERE / "runner.py").read_bytes()).hexdigest():
        return False
    expected = {name: expected_scenario(name, spec) for name, spec in WORLD["scenarios"].items()}
    if raw.get("scenarios") != expected:
        return False
    seen = set()
    for scenario in raw["scenarios"].values():
        for row in scenario["attempts"]:
            key = row["attempt_id"]
            if key in seen:
                return False
            seen.add(key)
    return len(seen) == sum(len(spec) - 2 for spec in WORLD["scenarios"].values()) * len(WORLD["sealed_variants"])


if not validate(RAW):
    raise SystemExit("FAIL_INDEPENDENT_AUDIT")

mutations = {}
missing = copy.deepcopy(RAW)
missing["scenarios"]["multiple_survivors"]["attempts"].pop()
mutations["missing_attempt"] = missing
duplicate = copy.deepcopy(RAW)
duplicate["scenarios"]["multiple_survivors"]["attempts"].append(
    copy.deepcopy(duplicate["scenarios"]["multiple_survivors"]["attempts"][0]))
mutations["duplicate_attempt"] = duplicate
repeat_sealed = copy.deepcopy(RAW)
repeat_sealed["scenarios"]["multiple_survivors"]["attempts"][0]["variant"] = "s3"
mutations["repeated_sealed_variant"] = repeat_sealed
family = copy.deepcopy(RAW)
family["scenarios"]["multiple_survivors"]["comparison_family"] = ["route_b"]
mutations["altered_comparison_family"] = family
safety = copy.deepcopy(RAW)
for row in safety["scenarios"]["fast_but_unsafe"]["attempts"]:
    row["forbidden"] = False
safety["scenarios"]["fast_but_unsafe"]["allowed_claim"] = "SURVIVOR_VS_BASELINE_ONLY"
mutations["forged_safety"] = safety
global_claim = copy.deepcopy(RAW)
global_claim["scenarios"]["screened_out_is_best"]["global_optimality_claim"] = True
global_claim["scenarios"]["screened_out_is_best"]["allowed_claim"] = "GLOBAL_BEST_CONFIRMED"
mutations["unsupported_global_best"] = global_claim
unadjusted = copy.deepcopy(RAW)
unadjusted["scenarios"]["multiple_survivors"]["allowed_claim"] = "ROUTE_B_PROMOTED_UNADJUSTED"
mutations["unadjusted_promotion"] = unadjusted
rejected = {name: not validate(mutant) for name, mutant in mutations.items()}
if not all(rejected.values()):
    raise SystemExit("FAIL_MUTATION_CONTROLS")

result = {
    "status": "PASS_CLAIM_BOUNDARY_SCOPED",
    "raw_sha256": hashlib.sha256(RAW_BYTES).hexdigest(),
    "attempt_count": len(seen),
    "scenario_labels": {name: value["allowed_claim"] for name, value in RAW["scenarios"].items()},
    "global_optimality_claims": sum(value["global_optimality_claim"] for value in RAW["scenarios"].values()),
    "mutation_controls": rejected,
    "scope": "authored finite deterministic claim-boundary fixtures only",
}
(HERE / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
