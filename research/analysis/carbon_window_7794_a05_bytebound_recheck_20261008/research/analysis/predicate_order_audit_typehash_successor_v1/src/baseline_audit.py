import copy
import json
import sys

PREDICATES = ("A", "B", "C", "D")
COST = {"A": 1, "B": 2, "C": 5, "D": 10}
EXPECTED_ORDERS = {"NAIVE": ["D", "C", "B", "A"], "FROZEN_COST_SELECTIVITY": ["A", "B", "C", "D"]}
EXPECTED_GRID = [round(i / 20, 2) for i in range(21)]


def replay(state, order):
    spent = 0
    visits = 0
    outcome = True
    for predicate in order:
        spent += COST[predicate]
        visits += 1
        if state[predicate] is False:
            outcome = False
            break
    return outcome, spent, visits


def weighted_quantile(values, quantile):
    ordered = sorted(values, key=lambda value: value["cost"])
    threshold = quantile * sum(value["weight"] for value in ordered)
    accumulated = 0.0
    for value in ordered:
        accumulated += value["weight"]
        if accumulated + 1e-12 >= threshold:
            return value["cost"]
    return max(value["cost"] for value in ordered)


def audit(doc, include_controls=True):
    errors = []
    if doc.get("schema") != "predicate-order-drift-raw-v1":
        errors.append("schema")
    if doc.get("predicates") != list(PREDICATES) or doc.get("cost") != COST or doc.get("orders") != EXPECTED_ORDERS:
        errors.append("frozen_constants")
    if doc.get("drift_grid") != EXPECTED_GRID or len(doc.get("distributions", [])) != len(EXPECTED_GRID):
        errors.append("grid")
    observed_crossover = None
    for index, distribution in enumerate(doc.get("distributions", [])):
        alpha = EXPECTED_GRID[index] if index < len(EXPECTED_GRID) else None
        if distribution.get("alpha") != alpha:
            errors.append(f"alpha:{index}")
            continue
        rows = distribution.get("rows", [])
        if len(rows) != 16 or [r.get("state_id") for r in rows] != list(range(16)):
            errors.append(f"state_space:{index}")
            continue
        total_weight = 0.0
        recomputed = {name: [] for name in EXPECTED_ORDERS}
        for row in rows:
            state = row.get("truth", {})
            expected_state = {name: bool(row["state_id"] & (1 << bit)) for bit, name in enumerate(PREDICATES)}
            if state != expected_state or row.get("expected") != all(expected_state.values()):
                errors.append(f"truth:{index}:{row['state_id']}")
            mask = row["state_id"]
            if mask == 14:
                expected_weight = 0.8 * (1 - alpha)
            elif mask == 7:
                expected_weight = 0.8 * alpha
            elif mask == 15:
                expected_weight = 0.2
            else:
                expected_weight = 0.0
            if abs(row.get("weight", -1) - expected_weight) > 1e-10:
                errors.append(f"weight:{index}:{mask}")
            total_weight += expected_weight
            for label, order in EXPECTED_ORDERS.items():
                decision, cost, visits = replay(expected_state, order)
                actual = row.get(label, {})
                if actual != {"decision": decision, "cost": cost, "evaluations": visits}:
                    errors.append(f"replay:{index}:{mask}:{label}")
                recomputed[label].append({"weight": expected_weight, "cost": cost, "evaluations": visits})
        if abs(total_weight - 1.0) > 1e-10:
            errors.append(f"mass:{index}")
        for label, values in recomputed.items():
            summary = distribution.get("summaries", {}).get(label, {})
            ec = sum(v["weight"] * v["cost"] for v in values)
            ee = sum(v["weight"] * v["evaluations"] for v in values)
            if abs(summary.get("expected_cost", -1) - ec) > 1e-9 or abs(summary.get("expected_evaluations", -1) - ee) > 1e-9:
                errors.append(f"summary:{index}:{label}")
            if summary.get("semantic_mismatches") != 0:
                errors.append(f"semantics:{index}:{label}")
            for metric, quantile in (("p50_row_cost", 0.50), ("p95_row_cost", 0.95), ("p99_row_cost", 0.99)):
                if summary.get(metric) != weighted_quantile(values, quantile):
                    errors.append(f"{metric}:{index}:{label}")
            if label == "FROZEN_COST_SELECTIVITY" and ec > sum(v["weight"] * v["cost"] for v in recomputed["NAIVE"]):
                if observed_crossover is None:
                    observed_crossover = alpha
    if doc.get("first_cost_crossover_alpha") != observed_crossover:
        errors.append("crossover")
    controls = {}
    if include_controls and not errors and doc.get("distributions"):
        mutants = {}
        m = copy.deepcopy(doc); m["first_cost_crossover_alpha"] = 0.0; mutants["verdict_crossover"] = m
        m = copy.deepcopy(doc); m["distributions"].pop(5); mutants["row_distribution_deleted"] = m
        m = copy.deepcopy(doc); m["distributions"][0]["rows"][0]["NAIVE"]["cost"] += 1; mutants["cost_mutation"] = m
        m = copy.deepcopy(doc); m["distributions"][1]["rows"].append(copy.deepcopy(m["distributions"][1]["rows"][0])); mutants["duplicate_state"] = m
        m = copy.deepcopy(doc); m["distributions"][10]["rows"][14]["weight"] += 0.1; mutants["mass_mutation"] = m
        for name, mutant in mutants.items():
            controls[name] = audit_without_controls(mutant)
    return {"status": "PASS_DRIFT_BOUNDARY_MAPPED" if not errors and len(controls) == 5 and all(controls.values()) else "HOLD_OR_FAIL", "errors": errors, "corruption_controls_rejected": sum(controls.values()), "corruption_control_count": len(controls), "corruption_controls": controls, "first_cost_crossover_alpha": observed_crossover, "distribution_count": len(doc.get("distributions", [])), "row_count": sum(len(d.get("rows", [])) for d in doc.get("distributions", []))}


def audit_without_controls(doc):
    # Run the independently reconstructed checks without recursively generating controls.
    return bool(audit(doc, include_controls=False)["errors"])


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        result = audit(json.load(f))
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_DRIFT_BOUNDARY_MAPPED" else 1)


