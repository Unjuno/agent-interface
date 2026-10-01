#!/usr/bin/env python3
"""Independent raw-only reconstruction of the frozen T0 candidate ledger."""
import argparse
import json
import math
import statistics

CASES = ("shared_level_only", "delta_positive", "delta_negative")
KS = (1, 5, 20)
BLOCKS = 300
MU_Y = 0.2
HIGH_COST = 100
LOW_COST = 1
CI_CRITICAL = 2.773  # Bonferroni two-sided family-wise 95% over 3 cases x 3 K values.


def corr(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    dx, dy = [x - mx for x in xs], [y - my for y in ys]
    den = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    return sum(x * y for x, y in zip(dx, dy)) / den if den else 0.0


def mean_ci(values):
    avg = statistics.mean(values)
    se = statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else float("inf")
    return {"mean": avg, "se": se, "lo95": avg - CI_CRITICAL * se,
            "hi95": avg + CI_CRITICAL * se, "critical_value": CI_CRITICAL,
            "familywise": "Bonferroni 95%, 9 case/K cells"}


def reconstruct(row):
    case, k = row["case"], row["k"]
    pilot, scored, extra, y_only, budget_x = (row[name] for name in ("pilot", "scored", "extra_x", "y_only", "budget_x"))
    if case not in CASES or k not in KS or not isinstance(row["block"], int):
        raise ValueError("bad case/K/block")
    if len(pilot) != 64 or len(scored) != 20 * k or len(extra) != 80 * k:
        raise ValueError("paired/cheap sample count mismatch")
    if len(y_only) != 21 * k + 64 or len(budget_x) != 64:
        raise ValueError("cost-control sample count mismatch")
    if any(len(item) != 6 for item in pilot + scored):
        raise ValueError("paired raw row must contain six independent values")
    for item in pilot + scored:
        dy, dx, yb, xb, yc, xc = item
        if not all(math.isfinite(v) for v in item) or abs((yc - yb) - dy) > 1e-10 or abs((xc - xb) - dx) > 1e-10:
            raise ValueError("non-finite or inconsistent arm/difference raw row")
    cv_cost = (len(pilot) + len(scored)) * (HIGH_COST + LOW_COST) + len(extra) * LOW_COST
    y_cost = len(y_only) * HIGH_COST + len(budget_x) * LOW_COST
    if cv_cost != y_cost:
        raise ValueError(f"cost mismatch: {cv_cost} != {y_cost}")
    px, py = [r[1] for r in pilot], [r[0] for r in pilot]
    mx, my = statistics.mean(px), statistics.mean(py)
    vx = sum((x - mx) ** 2 for x in px) / (len(px) - 1)
    beta = sum((x - mx) * (y - my) for x, y in zip(px, py)) / (len(px) - 1) / vx if vx else 0.0
    x_pair = [r[1] for r in scored]
    cv = statistics.mean(r[0] for r in scored) - beta * (statistics.mean(x_pair) - statistics.mean(extra))
    baseline = statistics.mean(y_only)
    level_r = corr([r[4] for r in scored], [r[5] for r in scored])
    delta_r = corr([r[0] for r in scored], [r[1] for r in scored])
    return {"case": case, "k": k, "block": row["block"], "beta": beta,
            "cv": cv, "y_only": baseline, "level_r": level_r, "delta_r": delta_r,
            "cv_se2": (cv - MU_Y) ** 2, "y_se2": (baseline - MU_Y) ** 2}


def audit(path):
    groups = {(case, k): [] for case in CASES for k in KS}
    with open(path, encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            row = json.loads(line)
            result = reconstruct(row)
            groups[(result["case"], result["k"])].append(result)
    errors = []
    summaries = []
    for case in CASES:
        for k in KS:
            rows = groups[(case, k)]
            if len(rows) != BLOCKS or sorted(r["block"] for r in rows) != list(range(BLOCKS)):
                errors.append(f"{case}/K{k}: block set/count mismatch ({len(rows)})")
                continue
            diffs = [r["cv_se2"] - r["y_se2"] for r in rows]
            dci = mean_ci(diffs)
            betaci = mean_ci([r["beta"] for r in rows])
            summary = {
                "case": case, "k": k, "blocks": len(rows),
                "mean_beta": betaci, "mean_level_correlation": statistics.mean(r["level_r"] for r in rows),
                "mean_difference_correlation": statistics.mean(r["delta_r"] for r in rows),
                "mse_cv": statistics.mean(r["cv_se2"] for r in rows),
                "mse_y_only": statistics.mean(r["y_se2"] for r in rows),
                "mse_difference_cv_minus_y": dci,
            }
            summary["relative_mse_reduction"] = 1.0 - summary["mse_cv"] / summary["mse_y_only"]
            summaries.append(summary)
    by_key = {(s["case"], s["k"]): s for s in summaries}
    shared = by_key.get(("shared_level_only", 20))
    if shared and (shared["mean_level_correlation"] < 0.95 or abs(shared["mean_difference_correlation"]) > 0.10
                   or abs(shared["mean_beta"]["mean"]) > 0.10 or shared["mse_difference_cv_minus_y"]["hi95"] < 0):
        errors.append("shared-level negative control failed its preregistered no-benefit/eligibility gate")
    for case in ("delta_positive", "delta_negative"):
        item = by_key.get((case, 20))
        if item and (abs(item["mean_difference_correlation"]) < 0.70
                     or item["mse_difference_cv_minus_y"]["hi95"] >= 0
                     or item["relative_mse_reduction"] < 0.05):
            errors.append(f"{case}: predictive signed-difference control did not show audited >=5% gain")
    return {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_GATE",
            "rows": sum(map(len, groups.values())), "groups": len(summaries),
            "cost_units_per_group_block": {"K1": 8564, "K5": 16964, "K20": 48464},
            "independent_raw_reconstruction": True, "errors": errors, "summaries": summaries}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.raw)
    with open(args.output, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"{result['disposition']} groups={result['groups']} rows={result['rows']} errors={len(result['errors'])}")
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
