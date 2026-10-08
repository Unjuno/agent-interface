#!/usr/bin/env python3
"""Frozen finite T1 candidate; no model, GUI, external effects, or random sampling."""
import hashlib, json, sys
from pathlib import Path

ALLOCATION = "SELECTION-TRANSPORT-5663-T1-20261002-01"
STRATA = ("easy", "hard")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rate(cell):
    successes, trials = cell
    if trials <= 0 or successes < 0 or successes > trials:
        return None
    return successes / trials


def weights(population):
    total = sum(population.get(s, 0) for s in STRATA)
    if total <= 0 or any(population.get(s, 0) < 0 for s in STRATA):
        return None
    return {s: population.get(s, 0) / total for s in STRATA}


def deltas(outcomes):
    result = {}
    for s in STRATA:
        a, b = rate(outcomes[s]["A"]), rate(outcomes[s]["B"])
        result[s] = None if a is None or b is None else b - a
    return result


def weighted(w, d):
    if w is None or any(d.get(s) is None for s in STRATA):
        return None
    return sum(w[s] * d[s] for s in STRATA)


def analyze(case):
    ws, wt = weights(case["source_population"]), weights(case["target_population"])
    ds, dt = deltas(case["source_outcomes"]), deltas(case["target_outcomes"])
    support = all(case["source_population"].get(s, 0) > 0 and case["target_population"].get(s, 0) > 0 and ds[s] is not None and dt[s] is not None for s in STRATA)
    comparable = case["source_endpoint"] == case["target_endpoint"]
    invariant = support and all(ds[s] == dt[s] for s in STRATA)
    source_direct, target_direct = weighted(ws, ds), weighted(wt, dt)
    naive = weighted(wt, ds) if support else None
    if not comparable:
        status, reason, transported = "HOLD_NONCOMPARABLE", "endpoint_contract_mismatch", None
    elif not support:
        status, reason, transported = "HOLD_NONTRANSPORTABLE", "positivity_or_cell_support_missing", None
    elif not invariant:
        status, reason, transported = "HOLD_NONTRANSPORTABLE", "conditional_route_effect_changed", None
    else:
        status, reason, transported = "TRANSPORT_METHOD_CONTROL_PASS", "support_and_conditional_effects_match", naive
    return {"status":status,"reason":reason,"source_direct_effect":source_direct,"target_direct_effect":target_direct,
            "conditional_effects_source":ds,"conditional_effects_target":dt,"common_support":support,
            "endpoint_comparable":comparable,"conditional_effect_invariant":invariant,"transported_effect":transported,
            "diagnostic_only_naive_standardization":naive if not invariant and support else None}


def run(doc):
    freeze=json.loads((Path(__file__).parent/"FREEZE.json").read_text(encoding="utf-8")); return {"schema":"selection-transport-t1-result-v1","allocation":ALLOCATION,"base_main_sha":freeze["base_main_sha"],"container_image_ref":freeze["container_image_ref"],"candidate_sha256":digest(__file__),
            "input_sha256":digest(Path(__file__).parent/"inputs"/"fixture.json"),
            "scenarios":{name:analyze(case) for name,case in doc["scenarios"].items()}}


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    doc = json.loads(src.read_text(encoding="utf-8"))
    out.write_text(json.dumps(run(doc),sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()