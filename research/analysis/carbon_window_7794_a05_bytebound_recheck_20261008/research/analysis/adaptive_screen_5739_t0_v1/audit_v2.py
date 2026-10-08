"""Versioned read-only raw auditor for Issue #5739; does not import or run candidate code."""
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORLD_BYTES = (HERE / "world.json").read_bytes()
RAW_BYTES = (HERE / "candidate_raw.json").read_bytes()
WORLD = json.loads(WORLD_BYTES)
RAW = json.loads(RAW_BYTES)
OUT = HERE / "audit_v2_result.json"
if OUT.exists():
    raise FileExistsError(OUT)


def expected_scenario(name, spec):
    attempts = []
    arms = sorted(set(spec) - {"family", "screened_out"})
    for arm in arms:
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
    elif len(family) > 1:
        label = "HOLD_MULTIPLE_COMPARISON_UNADJUSTED"
    elif screened_out:
        label = "SURVIVOR_VS_BASELINE_ONLY_NO_GLOBAL_OPTIMALITY"
    else:
        label = "SURVIVOR_VS_BASELINE_ONLY"
    return {
        "attempts": attempts,
        "comparison_family": family,
        "screened_out": screened_out,
        "allowed_claim": label,
        "global_optimality_claim": False,
    }


def audit(raw):
    if raw.get("schema") != "issue-5739-t0-raw-v1":
        return None
    if raw.get("world_sha256") != hashlib.sha256(WORLD_BYTES).hexdigest():
        return None
    if raw.get("runner_sha256") != hashlib.sha256((HERE / "runner.py").read_bytes()).hexdigest():
        return None
    if raw.get("scope") != "authored finite deterministic claim-boundary fixtures only":
        return None
    expected = {name: expected_scenario(name, spec) for name, spec in WORLD["scenarios"].items()}
    if raw.get("scenarios") != expected:
        return None
    attempt_ids = [row["attempt_id"] for item in raw["scenarios"].values() for row in item["attempts"]]
    if len(attempt_ids) != len(set(attempt_ids)):
        return None
    expected_count = sum(
        len(set(spec) - {"family", "screened_out"}) * len(WORLD["sealed_variants"])
        for spec in WORLD["scenarios"].values()
    )
    if len(attempt_ids) != expected_count:
        return None
    return {"attempt_count": len(attempt_ids), "expected_count": expected_count}


reconstruction = audit(RAW)
if reconstruction is None:
    raise SystemExit("FAIL_AUDIT_V2_RAW_RECONSTRUCTION")

mutations = {}
missing = copy.deepcopy(RAW)
missing["scenarios"]["multiple_survivors"]["attempts"].pop()
mutations["missing_attempt"] = missing
duplicate = copy.deepcopy(RAW)
duplicate["scenarios"]["multiple_survivors"]["attempts"].append(
    copy.deepcopy(duplicate["scenarios"]["multiple_survivors"]["attempts"][0]))
mutations["duplicate_attempt"] = duplicate
repeated = copy.deepcopy(RAW)
repeated["scenarios"]["multiple_survivors"]["attempts"][0]["variant"] = "s3"
mutations["repeated_sealed_variant"] = repeated
family = copy.deepcopy(RAW)
family["scenarios"]["multiple_survivors"]["comparison_family"] = ["route_b"]
mutations["altered_comparison_family"] = family
safety = copy.deepcopy(RAW)
for row in safety["scenarios"]["fast_but_unsafe"]["attempts"]:
    row["forbidden"] = False
safety["scenarios"]["fast_but_unsafe"]["allowed_claim"] = "SURVIVOR_VS_BASELINE_ONLY"
mutations["forged_safety"] = safety
global_best = copy.deepcopy(RAW)
global_best["scenarios"]["screened_out_is_best"]["global_optimality_claim"] = True
global_best["scenarios"]["screened_out_is_best"]["allowed_claim"] = "GLOBAL_BEST_CONFIRMED"
mutations["unsupported_global_best"] = global_best
promotion = copy.deepcopy(RAW)
promotion["scenarios"]["multiple_survivors"]["allowed_claim"] = "ROUTE_B_PROMOTED_UNADJUSTED"
mutations["unadjusted_promotion"] = promotion
rejected = {name: audit(mutant) is None for name, mutant in mutations.items()}
if not all(rejected.values()):
    raise SystemExit("FAIL_AUDIT_V2_MUTATION_CONTROLS")

result = {
    "status": "PASS_CLAIM_BOUNDARY_SCOPED",
    "audit_version": "v2-read-only",
    "predecessor_audit_disposition": "STOP_AUDITOR_REPORT_SERIALIZATION",
    "raw_sha256": hashlib.sha256(RAW_BYTES).hexdigest(),
    "world_sha256": hashlib.sha256(WORLD_BYTES).hexdigest(),
    "runner_sha256": hashlib.sha256((HERE / "runner.py").read_bytes()).hexdigest(),
    "audit_v1_sha256": hashlib.sha256((HERE / "audit.py").read_bytes()).hexdigest(),
    "attempt_count": reconstruction["attempt_count"],
    "scenario_labels": {name: value["allowed_claim"] for name, value in RAW["scenarios"].items()},
    "global_optimality_claims": sum(value["global_optimality_claim"] for value in RAW["scenarios"].values()),
    "mutation_controls": rejected,
    "scope": "authored finite deterministic claim-boundary fixtures only",
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
