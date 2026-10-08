#!/usr/bin/env python3
"""Independent raw-only auditor for #8654 C01; reads candidate JSONL on stdin."""
import itertools
import json
import math
import sys

N = 16
Q = 0.25
OUTCOMES = {
    "STABLE": {"cue": 1.0, "alt": 0.0},
    "REVERSAL": {"cue": 0.0, "alt": 1.0},
    "GLOBAL_SHIFT": {"cue": 0.0, "alt": -1.0},
}

def independent_mass(k):
    return math.comb(N, k) * (Q ** k) * ((1 - Q) ** (N - k))

def expected(regime, left_alt, right_alt):
    truth = OUTCOMES[regime]
    has_full_support = (0 < left_alt < N) and (0 < right_alt < N)
    observed_cue = 2 * N - left_alt - right_alt
    observed_alt = left_alt + right_alt
    mu_cue = (observed_cue * truth["cue"] / (1 - Q)) / (2 * N)
    mu_alt = (observed_alt * truth["alt"] / Q) / (2 * N)
    delta = mu_cue - mu_alt
    if not has_full_support:
        label = "UNIDENTIFIABLE"
    elif delta < 0:
        label = "REVERSAL"
    elif mu_cue > 0.5:
        label = "STABLE"
    else:
        label = "GLOBAL_SHIFT"
    return {
        "probability": independent_mass(left_alt) * independent_mass(right_alt),
        "supported": has_full_support,
        "cue_mean_ht": mu_cue,
        "alternative_mean_ht": mu_alt,
        "contrast_ht": delta,
        "decision": label,
        "oracle_contrast": truth["cue"] - truth["alt"],
    }

def validate(row):
    regime = row.get("regime")
    if regime not in OUTCOMES:
        return False
    k0, k1 = row.get("k0"), row.get("k1")
    if type(k0) is not int or type(k1) is not int or not (0 <= k0 <= N and 0 <= k1 <= N):
        return False
    want = expected(regime, k0, k1)
    return all(row.get(key) == value for key, value in want.items())

raw = [json.loads(line) for line in sys.stdin if line.strip()]
expected_keys = {(r, a, b) for r in OUTCOMES for a, b in itertools.product(range(N + 1), repeat=2)}
seen = {(x.get("regime"), x.get("k0"), x.get("k1")) for x in raw}
errors = []
if len(raw) != 867 or len(seen) != 867 or seen != expected_keys:
    errors.append("row identity/cardinality mismatch")
if any(not validate(row) for row in raw):
    errors.append("one or more rows disagree with independent reconstruction")
masses = {}
for regime in OUTCOMES:
    mass = math.fsum(x["probability"] for x in raw if x["regime"] == regime)
    masses[regime] = mass
    if abs(mass - 1.0) > 1e-12:
        errors.append(f"probability mass mismatch: {regime}={mass}")
    if any(x["decision"] != "UNIDENTIFIABLE" for x in raw if x["regime"] == regime and (x["k0"], x["k1"]) == (0, 0)):
        errors.append(f"greedy baseline did not abstain: {regime}")
mutations = [
    lambda x: {**x, "probability": x["probability"] + 0.01},
    lambda x: {**x, "supported": not x["supported"]},
    lambda x: {**x, "alternative_mean_ht": x["alternative_mean_ht"] + 1.0},
    lambda x: {**x, "decision": "STABLE" if x["decision"] != "STABLE" else "REVERSAL"},
]
probe = next((x for x in raw if x["regime"] == "REVERSAL" and x["k0"] == 8 and x["k1"] == 8), {})
rejected = sum(not validate(mutator(probe)) for mutator in mutations)
if rejected != len(mutations):
    errors.append(f"mutation controls rejected {rejected}/{len(mutations)}")
result = {
    "status": "PASS_CONSTRUCTION_SCOPED" if not errors else "FAIL_CONSTRUCTION",
    "rows": len(raw), "expected_rows": 867, "probability_mass": masses,
    "mutations_rejected": rejected, "mutations_total": len(mutations),
    "errors": errors, "scope": "deterministic finite method construction only",
}
print(json.dumps(result, sort_keys=True, indent=2))
sys.exit(0 if not errors else 1)
