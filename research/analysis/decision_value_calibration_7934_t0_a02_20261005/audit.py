#!/usr/bin/env python3
"""Independent raw-only calibration-boundary auditor for Issue #7934 A02."""
import hashlib
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))


def draw(qt, seed, stream):
    key = ("7934-T0-A02|qt=%s|seed=%s|stream=%s" % (qt, seed, stream)).encode("ascii")
    return int(hashlib.sha256(key).hexdigest()[:13], 16) / float(16**13)


def choose(name, qm, qt, cost):
    if name == "cost":
        return "ycheck"
    if name == "entropy":
        hx = 1.0 + qm * math.log2(qm) + (1.0 - qm) * math.log2(1.0 - qm)
        hy = 1.0
        return "ycheck" if hy >= hx else "xcheck"
    quality = qm if name == "decision_value" else qt
    return "xcheck" if abs(quality - 0.5) - cost > 1e-12 else None


def expected_signal(row):
    return row["x"] if draw(row["qt"], row["seed"], "noise") < row["qt"] else 1 - row["x"]


def route_x(row, check, policy):
    if check != "xcheck":
        return 0  # balanced X prior; tie-break route A
    q = row["qt"] if policy == "oracle" else row["qm"]
    return row["x_signal"] if q > 0.5 else 1 - row["x_signal"]


def exact_metrics(qt, qm, cost, policy, check):
    if check == "xcheck":
        q = qt if policy == "oracle" else qm
        regret = 1.0 - qt if q > 0.5 else qt
        charge = cost
    elif check == "ycheck":
        regret, charge = 0.5, CFG["nuisance_cost"]
    else:
        regret, charge = 0.5, 0.0
    return regret, charge, regret + charge


def unknown_control(*, shifted=False, unknown_mass=0.0):
    return {"status": "UNKNOWN", "check": None, "checks_performed": 0} \
        if shifted or unknown_mass > 0 else {"status": "READY", "check": None,
                                            "checks_performed": 0}


def main(raw_path, result_path, outdir):
    raw_bytes = pathlib.Path(raw_path).read_bytes()
    result = json.loads(pathlib.Path(result_path).read_text(encoding="utf-8"))
    rows = [json.loads(x) for x in raw_bytes.decode("utf-8").splitlines() if x]
    errors, lookup = [], {}
    expected_n = 4 * 4 * 2 * CFG["seed_count_per_cell"]
    if len(rows) != expected_n or result.get("observations") != expected_n:
        errors.append("observation_count")
    if hashlib.sha256(raw_bytes).hexdigest() != result.get("raw_sha256"):
        errors.append("raw_digest")
    for r in rows:
        key = (r.get("qt"), r.get("qm"), r.get("x_cost"), r.get("seed"))
        if key in lookup:
            errors.append("duplicate_row:%s" % (key,))
        lookup[key] = r
        qt, qm, cost, seed = key
        if qt not in CFG["q_values"] or qm not in CFG["q_values"] or cost not in CFG["direct_costs"]:
            errors.append("grid_value:%s" % (key,))
            continue
        if not (CFG["seed_start"] <= seed < CFG["seed_start"] + CFG["seed_count_per_cell"]):
            errors.append("seed_range:%s" % (key,))
            continue
        x = int(draw(qt, seed, "x") >= 0.5)
        y = int(draw(qt, seed, "y") >= 0.5)
        signal = x if draw(qt, seed, "noise") < qt else 1 - x
        if (r.get("x"), r.get("y"), r.get("x_signal")) != (x, y, signal):
            errors.append("raw_draw:%s" % (key,))
    if len(lookup) != expected_n:
        errors.append("unique_row_count")
    cells = result.get("cells", [])
    if len(cells) != 32 or result.get("cell_count") != 32:
        errors.append("cell_count")
    checked_cells, adverse, opposed = 0, [], []
    calibrated = 0
    for cell in cells:
        qt, qm, cost = cell.get("qt"), cell.get("qm"), cell.get("x_cost")
        if cell.get("n") != CFG["seed_count_per_cell"]:
            errors.append("cell_n:%s:%s:%s" % (qt, qm, cost))
        summary = cell.get("policies", {})
        sampled = {p: {"regret": 0, "cost": 0.0, "gates": 0} for p in CFG["policies"]}
        for i in range(CFG["seed_count_per_cell"]):
            seed = CFG["seed_start"] + i
            row = lookup.get((qt, qm, cost, seed))
            if row is None:
                errors.append("missing_cell_row:%s:%s:%s:%s" % (qt, qm, cost, seed))
                continue
            for policy in CFG["policies"]:
                check = choose(policy, qm, qt, cost)
                px = route_x(row, check, policy)
                regret = int(px != row["x"])
                sampled[policy]["regret"] += regret
                sampled[policy]["cost"] += (cost if check == "xcheck" else
                                              CFG["nuisance_cost"] if check == "ycheck" else 0.0)
                sampled[policy]["gates"] += int(px not in (0, 1))
        expected_checks = {p: choose(p, qm, qt, cost) for p in CFG["policies"]}
        for policy in CFG["policies"]:
            got = summary.get(policy, {})
            check = expected_checks[policy]
            if got.get("selected_check") != check:
                errors.append("selection:%s:%s:%s:%s" % (qt, qm, cost, policy))
            vals = sampled[policy]
            mr, mc = vals["regret"] / CFG["seed_count_per_cell"], vals["cost"] / CFG["seed_count_per_cell"]
            if abs(got.get("mean_realized_regret", -1) - mr) > 1e-12:
                errors.append("sample_regret:%s:%s:%s:%s" % (qt, qm, cost, policy))
            if abs(got.get("mean_check_cost", -1) - mc) > 1e-12:
                errors.append("sample_cost:%s:%s:%s:%s" % (qt, qm, cost, policy))
            if got.get("hard_gate_violations") != vals["gates"] or vals["gates"] != 0:
                errors.append("hard_gate:%s:%s:%s:%s" % (qt, qm, cost, policy))
            er, ec, el = exact_metrics(qt, qm, cost, policy, check)
            if (abs(got.get("exact_expected_regret", -1) - er) > 1e-12 or
                    abs(got.get("exact_expected_cost", -1) - ec) > 1e-12 or
                    abs(got.get("exact_expected_total_loss", -1) - el) > 1e-12):
                errors.append("exact_loss:%s:%s:%s:%s" % (qt, qm, cost, policy))
        if qm == qt:
            calibrated += 1
            d, o = summary["decision_value"], summary["oracle"]
            if d["selected_check"] != o["selected_check"]:
                errors.append("calibrated_selection:%s:%s" % (qt, cost))
            if abs(d["exact_expected_total_loss"] - o["exact_expected_total_loss"]) > 1e-12:
                errors.append("calibrated_loss:%s:%s" % (qt, cost))
        dv, co, en = summary["decision_value"], summary["cost"], summary["entropy"]
        if dv["mean_realized_regret"] > min(co["mean_realized_regret"], en["mean_realized_regret"]):
            adverse.append({"qt": qt, "qm": qm, "x_cost": cost,
                            "dv_regret": dv["mean_realized_regret"],
                            "baseline_regret": min(co["mean_realized_regret"], en["mean_realized_regret"])})
        if (qm > 0.5 and qt < 0.5) or (qm < 0.5 and qt > 0.5):
            if dv["selected_check"] == "xcheck":
                opposed.append({"qt": qt, "qm": qm, "x_cost": cost,
                                "dv_regret": dv["mean_realized_regret"]})
        checked_cells += 1
    ctrls = result.get("controls", {})
    expected_controls = {
        "distribution_shift": unknown_control(shifted=True),
        "unknown_mass_0_10": unknown_control(unknown_mass=0.10),
    }
    if ctrls != expected_controls:
        errors.append("unknown_controls")
    if calibrated != 8:
        errors.append("calibration_cell_count")
    report = {
        "status": "PASS_CALIBRATION_BOUNDARY" if not errors else "FAIL_AUDIT",
        "observations_reaudited": len(rows), "cells_reaudited": checked_cells,
        "calibrated_cells": calibrated, "independent_errors": errors,
        "decision_value_adverse_vs_both_baselines_cells": adverse,
        "opposed_likelihood_cells_where_direct_check_was_selected": opposed,
        "marked_controls_return_unknown": ctrls == expected_controls,
        "hard_gate_violations": 0,
    }
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "independent_audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                                   encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors),
                      "observations": len(rows), "cells": checked_cells,
                      "adverse_cells": len(adverse), "opposed_cells": len(opposed)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
