"""Additive strict, raw-only auditor for predicate-order retained evidence."""
from __future__ import annotations

import math

PREDICATES = ("A", "B", "C", "D")
COST = {"A": 1, "B": 2, "C": 5, "D": 10}
ORDERS = {
    "NAIVE": ("D", "C", "B", "A"),
    "FROZEN_COST_SELECTIVITY": ("A", "B", "C", "D"),
}
GRID = tuple(round(i / 20, 2) for i in range(21))


class AuditReject(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AuditReject(reason)


def reject_nonfinite(token: str):
    raise AuditReject("non-standard/non-finite JSON constant: " + token)


def strict_load(raw: bytes):
    import json
    return json.loads(raw.decode("utf-8"), parse_constant=reject_nonfinite)


def expected_weight(mask: int, alpha: float) -> float:
    if mask == 14:
        return 0.8 * (1.0 - alpha)
    if mask == 7:
        return 0.8 * alpha
    if mask == 15:
        return 0.2
    return 0.0


def require_valid_weight(value, expected: float) -> float:
    require(type(value) in (int, float), "weight_type")
    require(math.isfinite(value), "weight_finite")
    require(value == expected, "weight_binding")
    return value


def replay(state: dict[str, bool], order: tuple[str, ...]):
    cost = 0
    evaluations = 0
    decision = True
    for predicate in order:
        cost += COST[predicate]
        evaluations += 1
        if state[predicate] is False:
            decision = False
            break
    return {"decision": decision, "cost": cost, "evaluations": evaluations}


def weighted_quantile(rows: list[dict], q: float):
    ordered = sorted(rows, key=lambda row: row["cost"])
    total = sum(row["weight"] for row in ordered)
    threshold = q * total
    cumulative = 0.0
    for row in ordered:
        cumulative += row["weight"]
        if cumulative + 1e-12 >= threshold:
            return row["cost"]
    return max(row["cost"] for row in ordered)


def audit_document(doc: dict) -> dict:
    require(isinstance(doc, dict), "document must be an object")
    require(doc.get("schema") == "predicate-order-drift-raw-v1", "schema")
    require(doc.get("predicates") == list(PREDICATES), "predicates")
    require(doc.get("cost") == COST, "cost")
    require(doc.get("orders") == {k: list(v) for k, v in ORDERS.items()}, "orders")
    development_alpha = doc.get("development_alpha")
    require(type(development_alpha) in (int, float) and
            math.isfinite(development_alpha) and development_alpha == 0.0,
            "development_alpha")
    require(type(doc.get("truth_state_count")) is int and doc["truth_state_count"] == 16,
            "truth_state_count")
    require(doc.get("drift_grid") == list(GRID), "drift_grid")
    distributions = doc.get("distributions")
    require(isinstance(distributions, list) and len(distributions) == len(GRID),
            "distribution_count")

    crossover = None
    rows_checked = 0
    for index, distribution in enumerate(distributions):
        alpha = GRID[index]
        require(distribution.get("alpha") == alpha, f"alpha:{index}")
        rows = distribution.get("rows")
        require(isinstance(rows, list) and len(rows) == 16, f"rows:{index}")
        require([row.get("state_id") for row in rows] == list(range(16)),
                f"state_ids:{index}")
        mass = 0.0
        recomputed = {label: [] for label in ORDERS}
        for row in rows:
            mask = row["state_id"]
            state = {name: bool(mask & (1 << bit))
                     for bit, name in enumerate(PREDICATES)}
            require(row.get("truth") == state, f"truth:{index}:{mask}")
            require(row.get("expected") is all(state.values()),
                    f"expected:{index}:{mask}")
            wanted = expected_weight(mask, alpha)
            weight = require_valid_weight(row.get("weight"), wanted)
            mass += weight
            for label, order in ORDERS.items():
                got = replay(state, order)
                require(row.get(label) == got, f"replay:{index}:{mask}:{label}")
                recomputed[label].append(
                    {"weight": weight, "cost": got["cost"],
                     "evaluations": got["evaluations"]})
            rows_checked += 1
        require(abs(mass - 1.0) <= 1e-10, f"mass:{index}")
        summaries = distribution.get("summaries")
        require(isinstance(summaries, dict), f"summaries:{index}")
        for label, values in recomputed.items():
            summary = summaries.get(label, {})
            expected_cost = sum(x["weight"] * x["cost"] for x in values)
            expected_evals = sum(x["weight"] * x["evaluations"] for x in values)
            require(summary.get("expected_cost") == round(expected_cost, 12),
                    f"expected_cost:{index}:{label}")
            require(summary.get("expected_evaluations") == round(expected_evals, 12),
                    f"expected_evaluations:{index}:{label}")
            require(summary.get("semantic_mismatches") == 0,
                    f"semantic_mismatches:{index}:{label}")
            for metric, q in (("p50_row_cost", 0.5),
                              ("p95_row_cost", 0.95),
                              ("p99_row_cost", 0.99)):
                require(summary.get(metric) == weighted_quantile(values, q),
                        f"{metric}:{index}:{label}")
            if (label == "FROZEN_COST_SELECTIVITY" and
                    expected_cost > sum(x["weight"] * x["cost"]
                                        for x in recomputed["NAIVE"]) and
                    crossover is None):
                crossover = alpha
    require(doc.get("first_cost_crossover_alpha") == crossover, "crossover")
    require(rows_checked == 336, "row_total")
    return {
        "status": "PASS_AUDIT_HARDENING_SCOPED",
        "errors": [],
        "rows": rows_checked,
        "distributions": len(distributions),
        "first_cost_crossover_alpha": crossover,
    }
