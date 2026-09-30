import json
from pathlib import Path

PREDICATES = ("A", "B", "C", "D")
COST = {"A": 1, "B": 2, "C": 5, "D": 10}
ORDERS = {"NAIVE": ("D", "C", "B", "A"), "FROZEN_COST_SELECTIVITY": ("A", "B", "C", "D")}
GRID = tuple(i / 20 for i in range(21))


def eval_order(state, order):
    seen = []
    for name in order:
        seen.append(name)
        if state[name] is False:
            return False, sum(COST[n] for n in seen), len(seen)
    return True, sum(COST[n] for n in seen), len(seen)


def weighted_quantile(rows, q):
    target = q * sum(r["weight"] for r in rows)
    cumulative = 0.0
    for row in sorted(rows, key=lambda x: x["cost"]):
        cumulative += row["weight"]
        if cumulative + 1e-12 >= target:
            return row["cost"]
    return max(r["cost"] for r in rows)


def main(out):
    states = [dict(zip(PREDICATES, (bool(mask & (1 << i)) for i in range(4)))) for mask in range(16)]
    distributions = []
    for alpha in GRID:
        rows = []
        for mask, state in enumerate(states):
            if state == {"A": False, "B": True, "C": True, "D": True}:
                weight = 0.8 * (1.0 - alpha)
                stratum = "EARLY_A_REJECT"
            elif state == {"A": True, "B": True, "C": True, "D": False}:
                weight = 0.8 * alpha
                stratum = "LATE_D_REJECT"
            elif all(state.values()):
                weight = 0.2
                stratum = "ALL_TRUE"
            else:
                weight = 0.0
                stratum = "ZERO_MASS_STATE"
            expected = all(state.values())
            row = {"state_id": mask, "truth": state, "expected": expected, "weight": round(weight, 12), "stratum": stratum}
            for label, order in ORDERS.items():
                decision, cost, count = eval_order(state, order)
                row[label] = {"decision": decision, "cost": cost, "evaluations": count}
            rows.append(row)
        summaries = {}
        for label in ORDERS:
            weighted_cost = sum(r["weight"] * r[label]["cost"] for r in rows)
            weighted_evals = sum(r["weight"] * r[label]["evaluations"] for r in rows)
            summaries[label] = {
                "expected_cost": round(weighted_cost, 12),
                "expected_evaluations": round(weighted_evals, 12),
                "p50_row_cost": weighted_quantile([{"weight": r["weight"], "cost": r[label]["cost"]} for r in rows], 0.50),
                "p95_row_cost": weighted_quantile([{"weight": r["weight"], "cost": r[label]["cost"]} for r in rows], 0.95),
                "p99_row_cost": weighted_quantile([{"weight": r["weight"], "cost": r[label]["cost"]} for r in rows], 0.99),
                "semantic_mismatches": sum(r[label]["decision"] != r["expected"] for r in rows),
            }
        distributions.append({"alpha": round(alpha, 2), "rows": rows, "summaries": summaries})
    crossover = next((d["alpha"] for d in distributions if d["summaries"]["FROZEN_COST_SELECTIVITY"]["expected_cost"] > d["summaries"]["NAIVE"]["expected_cost"]), None)
    doc = {"schema": "predicate-order-drift-raw-v1", "predicates": PREDICATES, "cost": COST, "orders": {k: list(v) for k, v in ORDERS.items()}, "development_alpha": 0.0, "drift_grid": [round(x, 2) for x in GRID], "truth_state_count": 16, "distributions": distributions, "first_cost_crossover_alpha": crossover}
    Path(out).write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys
    main(sys.argv[1])

