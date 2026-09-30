#!/usr/bin/env python3
"""Frozen synthetic adaptive randomized-response composition experiment."""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

SEED_BASE = 54200930
PAIRS = 2048
MAX_QUERIES = 8
FILTER_EPSILON = 1.2
GLOBAL_QUERY_LIMIT = 3
STOP_LLR = 2.4
CHANNEL_EPSILON = {"rr-mild": 0.4, "rr-strong": 0.8}
POLICIES = ("STATIC_PER_CALL", "GLOBAL_QUERY_CAP", "SYMBOLIC_ODOMETER",
            "ADAPTIVE_EPSILON_FILTER", "PREDICATE_ONLY")


def make_inputs():
    rows = []
    for pair_id in range(PAIRS):
        rng = random.Random(SEED_BASE + pair_id * 7919)
        ready = int(rng.random() < 0.5)
        uniforms = [rng.random() for _ in range(MAX_QUERIES)]
        for secret in (0, 1):
            rows.append({"pair_id": pair_id, "secret": secret,
                         "task_ready": ready, "uniforms": uniforms})
    return rows


def choose_route(responses):
    if not responses:
        return "rr-mild"
    if len(responses) == 1:
        return "rr-strong" if responses[-1] == 1 else "rr-mild"
    return "rr-strong" if responses[-1] == responses[-2] else "rr-mild"


def run_one(event, policy):
    responses, routes, increments, llr_steps = [], [], [], []
    accounting_decisions = []
    eps_spent = 0.0
    rejected = False
    stop_reason = None
    for j in range(MAX_QUERIES):
        if policy == "PREDICATE_ONLY":
            stop_reason = "NO_SECRET_QUERY"
            break
        if policy == "GLOBAL_QUERY_CAP" and len(responses) >= GLOBAL_QUERY_LIMIT:
            stop_reason = "GLOBAL_QUERY_COUNT_LIMIT"
            break
        route = choose_route(responses)
        epsilon = CHANNEL_EPSILON[route]
        if policy == "ADAPTIVE_EPSILON_FILTER" and eps_spent + epsilon > FILTER_EPSILON + 1e-12:
            accounting_decisions.append({"route": route, "budget_before": round(eps_spent, 12),
                                         "query_epsilon": epsilon, "admitted": False})
            rejected = True
            stop_reason = "FILTER_BUDGET"
            break
        if policy == "SYMBOLIC_ODOMETER":
            accounting_decisions.append({"route": route, "budget_before": round(eps_spent, 12),
                                         "query_epsilon": epsilon, "admitted": True})
        elif policy == "ADAPTIVE_EPSILON_FILTER":
            accounting_decisions.append({"route": route, "budget_before": round(eps_spent, 12),
                                         "query_epsilon": epsilon, "admitted": True})
        p_true = math.exp(epsilon) / (1.0 + math.exp(epsilon))
        p_one = p_true if event["secret"] == 1 else 1.0 - p_true
        answer = int(event["uniforms"][j] < p_one)
        increment = epsilon if answer == 1 else -epsilon
        routes.append(route)
        responses.append(answer)
        increments.append(epsilon)
        llr_steps.append(increment)
        eps_spent += epsilon
        if abs(sum(llr_steps)) >= STOP_LLR:
            stop_reason = "POSTERIOR_THRESHOLD"
            break
    if stop_reason is None:
        stop_reason = "MAX_QUERY_LIMIT"
    llr = sum(llr_steps)
    prediction_credit = 1.0 if llr > 0 and event["secret"] == 1 else 1.0 if llr < 0 and event["secret"] == 0 else 0.5
    return {"pair_id": event["pair_id"], "secret": event["secret"], "policy": policy,
            "task_ready": event["task_ready"], "public_predicate_released": True,
            "task_completed": bool(event["task_ready"]), "routes": routes,
            "responses": responses, "epsilon_increments": increments,
            "llr_increments": llr_steps, "composed_epsilon": round(eps_spent, 12),
            "odometer_visible": policy in ("SYMBOLIC_ODOMETER", "ADAPTIVE_EPSILON_FILTER"),
            "accounting_decisions": accounting_decisions,
            "privacy_loss_llr": round(llr, 12), "filter_rejected_next_query": rejected,
            "stop_reason": stop_reason, "distinguisher_credit": prediction_credit}


def summarize(outcomes):
    groups = defaultdict(list)
    for row in outcomes:
        groups[row["policy"]].append(row)
    result = []
    for policy in POLICIES:
        rows = groups[policy]
        eps = [r["composed_epsilon"] for r in rows]
        result.append({"policy": policy, "episodes": len(rows), "pairs": len(rows) // 2,
                       "secret_queries": sum(len(r["routes"]) for r in rows),
                       "mean_queries": round(sum(len(r["routes"]) for r in rows) / len(rows), 6),
                       "max_queries": max(map(lambda r: len(r["routes"]), rows)),
                       "max_composed_epsilon": max(eps),
                       "mean_composed_epsilon": round(sum(eps) / len(eps), 6),
                       "episodes_over_1_2": sum(e > FILTER_EPSILON + 1e-12 for e in eps),
                       "filter_rejections": sum(r["filter_rejected_next_query"] for r in rows),
                       "max_abs_llr": max(abs(r["privacy_loss_llr"]) for r in rows),
                       "distinguisher_accuracy": round(sum(r["distinguisher_credit"] for r in rows) / len(rows), 6),
                       "task_completions": sum(r["task_completed"] for r in rows),
                       "task_ready": sum(r["task_ready"] for r in rows),
                       "predicate_releases": sum(r["public_predicate_released"] for r in rows)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    inputs = make_inputs()
    outcomes = [run_one(event, policy) for event in inputs for policy in POLICIES]
    for name, rows in (("inputs.jsonl", inputs), ("outcomes.jsonl", outcomes)):
        with (outdir / name).open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {"seed_base": SEED_BASE, "pairs": PAIRS, "episodes": len(inputs),
               "outcome_rows": len(outcomes), "filter_epsilon": FILTER_EPSILON,
               "global_query_limit": GLOBAL_QUERY_LIMIT, "groups": summarize(outcomes)}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"episodes": len(inputs), "outcome_rows": len(outcomes),
                      "groups": summary["groups"]}, sort_keys=True))


if __name__ == "__main__":
    main()
