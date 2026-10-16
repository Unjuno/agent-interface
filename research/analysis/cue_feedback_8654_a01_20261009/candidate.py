#!/usr/bin/env python3
"""Frozen candidate for #8654 C01. Emits exact finite support worlds as JSONL."""
import itertools
import json
import math

N = 16
P_ALT = 0.25
REGIMES = {
    "STABLE": (1.0, 0.0),
    "REVERSAL": (0.0, 1.0),
    "GLOBAL_SHIFT": (0.0, -1.0),
}

def binom_pmf(n, k, p):
    return math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))

for regime, (y_cue, y_alt) in REGIMES.items():
    for k0, k1 in itertools.product(range(N + 1), repeat=2):
        probability = binom_pmf(N, k0, P_ALT) * binom_pmf(N, k1, P_ALT)
        supported = all(0 < k < N for k in (k0, k1))
        cue_n = (N - k0) + (N - k1)
        alt_n = k0 + k1
        cue_mean = (cue_n * y_cue / (1.0 - P_ALT)) / (2 * N)
        alt_mean = (alt_n * y_alt / P_ALT) / (2 * N)
        contrast = cue_mean - alt_mean
        if not supported:
            decision = "UNIDENTIFIABLE"
        elif contrast < 0.0:
            decision = "REVERSAL"
        elif cue_mean > 0.5:
            decision = "STABLE"
        else:
            decision = "GLOBAL_SHIFT"
        row = {
            "regime": regime, "k0": k0, "k1": k1,
            "probability": probability, "supported": supported,
            "cue_mean_ht": cue_mean, "alternative_mean_ht": alt_mean,
            "contrast_ht": contrast, "decision": decision,
            "oracle_contrast": y_cue - y_alt,
        }
        print(json.dumps(row, sort_keys=True, separators=(",", ":")))
