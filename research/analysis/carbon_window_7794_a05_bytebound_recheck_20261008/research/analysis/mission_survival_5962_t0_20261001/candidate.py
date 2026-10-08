"""Exact path enumerator for Issue #5962 synthetic mission-survival T0."""
from fractions import Fraction
from itertools import product
import json

KERNELS = {
    "iid": {"S": Fraction(1, 5), "F": Fraction(1, 5)},
    "clustered": {"S": Fraction(1, 20), "F": Fraction(4, 5)},
    "alternating": {"S": Fraction(1, 4), "F": Fraction(0, 1)},
}
INITIAL_F = Fraction(1, 5)
LENGTHS = range(1, 9)


def probability(kernel, path):
    p = INITIAL_F if path[0] == "F" else 1 - INITIAL_F
    for prior, current in zip(path, path[1:]):
        p *= kernel[prior] if current == "F" else 1 - kernel[prior]
    return p


def endpoint(path, mode):
    if mode == "any_failure":
        stop = path.find("F")
        return ("FAIL" if stop >= 0 else "SURVIVE", stop + 1 if stop >= 0 else len(path))
    for i in range(len(path) - 1):
        if path[i:i + 2] == "FF":
            return "FAIL", i + 2
    return "SURVIVE", len(path)


def generate():
    rows = []
    for name, kernel in KERNELS.items():
        for n in LENGTHS:
            for bits in product("SF", repeat=n):
                path = "".join(bits)
                endpoints = {}
                for mode in ("any_failure", "failure_burst_2"):
                    verdict, observed = endpoint(path, mode)
                    endpoints[mode] = {
                        "verdict": verdict,
                        "observed": observed,
                        "censored": n - observed,
                        "retained_in_denominator": True,
                    }
                max_run = max((len(run) for run in path.split("S")), default=0)
                rows.append({
                    "kernel": name,
                    "n": n,
                    "path": path,
                    "probability": str(probability(kernel, path)),
                    "endpoints": endpoints,
                    "potential_max_failure_run": max_run,
                })
    return {"schema": "issue5962-mission-survival-t0-v1", "rows": rows}


if __name__ == "__main__":
    print(json.dumps(generate(), sort_keys=True, separators=(",", ":")))
