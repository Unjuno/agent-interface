#!/usr/bin/env python3
"""Frozen calibration-boundary simulator for Issue #7934 successor A02."""
import hashlib
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))


def uniform(qt, seed, stream):
    key = ("7934-T0-A02|qt=%s|seed=%s|stream=%s" % (qt, seed, stream)).encode("ascii")
    return int(hashlib.sha256(key).hexdigest()[:13], 16) / float(16**13)


def mutual_information(q):
    if q in (0.0, 1.0):
        return 1.0
    return 1.0 + q * math.log2(q) + (1.0 - q) * math.log2(1.0 - q)


def policy_selection(qm, qt, cost, name):
    if name == "cost":
        return "ycheck"
    if name == "entropy":
        info_x = mutual_information(qm)
        info_y = 1.0
        return "ycheck" if info_y >= info_x else "xcheck"
    if name == "decision_value":
        return "xcheck" if abs(qm - 0.5) - cost > 1e-12 else None
    if name == "oracle":
        return "xcheck" if abs(qt - 0.5) - cost > 1e-12 else None
    raise ValueError(name)


def predicted_x(signal, accuracy):
    return signal if accuracy > 0.5 else 1 - signal


def guarded_control(*, distribution_shift=False, unknown_mass=0.0):
    if distribution_shift or unknown_mass > 0:
        return {"status": "UNKNOWN", "check": None, "checks_performed": 0}
    return {"status": "READY", "check": None, "checks_performed": 0}


def run(outdir):
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    raw_rows = []
    cells = []
    for qt in CFG["q_values"]:
        for qm in CFG["q_values"]:
            for cost in CFG["direct_costs"]:
                seeds = []
                per_policy = {name: [] for name in CFG["policies"]}
                selections = {name: policy_selection(qm, qt, cost, name)
                              for name in CFG["policies"]}
                for i in range(CFG["seed_count_per_cell"]):
                    seed = CFG["seed_start"] + i
                    x = int(uniform(qt, seed, "x") >= 0.5)
                    y = int(uniform(qt, seed, "y") >= 0.5)
                    signal = x if uniform(qt, seed, "noise") < qt else 1 - x
                    row = {"qt": qt, "qm": qm, "x_cost": cost, "seed": seed,
                           "x": x, "y": y, "x_signal": signal}
                    raw_rows.append(row)
                    seeds.append(row)
                    for name, check in selections.items():
                        if check == "xcheck":
                            accuracy = qt if name == "oracle" else qm
                            route_x = predicted_x(signal, accuracy)
                            check_cost = cost
                        else:
                            route_x = 0
                            check_cost = CFG["nuisance_cost"] if check == "ycheck" else 0.0
                        regret = int(route_x != x)
                        per_policy[name].append({"regret": regret, "cost": check_cost,
                                                 "gate_violation": False})
                policy_metrics = {}
                for name, check in selections.items():
                    vals = per_policy[name]
                    if check == "xcheck":
                        acc = qt if name == "oracle" else qm
                        exact_regret = 1.0 - qt if acc > 0.5 else qt
                        exact_cost = cost
                    elif check == "ycheck":
                        exact_regret = 0.5
                        exact_cost = CFG["nuisance_cost"]
                    else:
                        exact_regret = 0.5
                        exact_cost = 0.0
                    policy_metrics[name] = {
                        "selected_check": check,
                        "mean_realized_regret": sum(v["regret"] for v in vals) / len(vals),
                        "mean_check_cost": sum(v["cost"] for v in vals) / len(vals),
                        "hard_gate_violations": sum(v["gate_violation"] for v in vals),
                        "exact_expected_regret": exact_regret,
                        "exact_expected_cost": exact_cost,
                        "exact_expected_total_loss": exact_regret + exact_cost,
                    }
                cells.append({"qt": qt, "qm": qm, "x_cost": cost,
                              "n": len(seeds), "policies": policy_metrics})
    raw_path = outdir / "raw_observations.jsonl"
    raw_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in raw_rows),
                        encoding="utf-8")
    result = {
        "allocation": "7934-T0-A02", "cells": cells,
        "cell_count": len(cells), "observations": len(raw_rows),
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "controls": {
            "distribution_shift": guarded_control(distribution_shift=True),
            "unknown_mass_0_10": guarded_control(unknown_mass=0.10),
        },
    }
    (outdir / "candidate_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SIMULATOR_COMPLETE", "cells": len(cells),
                      "observations": len(raw_rows), "raw_sha256": result["raw_sha256"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(run(sys.argv[1]))
