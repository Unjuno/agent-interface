#!/usr/bin/env python3
"""Independent replay audit for the frozen #5420 synthetic RR experiment."""
import hashlib
import json
import math
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

NAMES = ("STATIC_PER_CALL", "GLOBAL_QUERY_CAP", "SYMBOLIC_ODOMETER",
         "ADAPTIVE_EPSILON_FILTER", "PREDICATE_ONLY")
EPS = {"rr-mild": 0.4, "rr-strong": 0.8}


def next_route(history):
    n = len(history)
    if n == 0:
        return "rr-mild"
    if n == 1:
        return "rr-strong" if history[0] else "rr-mild"
    return "rr-strong" if history[-1] == history[-2] else "rr-mild"


def reconstruct(event, policy):
    history, channel_rows, likelihood_rows = [], [], []
    accounting_decisions = []
    total = 0.0
    refused = False
    reason = "MAX_QUERY_LIMIT"
    for index in range(8):
        if policy == "PREDICATE_ONLY":
            reason = "NO_SECRET_QUERY"
            break
        if policy == "GLOBAL_QUERY_CAP" and index >= 3:
            reason = "GLOBAL_QUERY_COUNT_LIMIT"
            break
        channel = next_route(history)
        cost = EPS[channel]
        if policy == "ADAPTIVE_EPSILON_FILTER" and total + cost > 1.2 + 1e-12:
            accounting_decisions.append({"route": channel, "budget_before": round(total, 12),
                                         "query_epsilon": cost, "admitted": False})
            refused = True
            reason = "FILTER_BUDGET"
            break
        if policy in ("SYMBOLIC_ODOMETER", "ADAPTIVE_EPSILON_FILTER"):
            accounting_decisions.append({"route": channel, "budget_before": round(total, 12),
                                         "query_epsilon": cost, "admitted": True})
        odds = math.exp(cost)
        probability_of_one = odds / (odds + 1.0) if event["secret"] else 1.0 / (odds + 1.0)
        observed = 1 if event["uniforms"][index] < probability_of_one else 0
        signed_loss = cost if observed == 1 else -cost
        history.append(observed)
        channel_rows.append(channel)
        likelihood_rows.append(signed_loss)
        total += cost
        if abs(sum(likelihood_rows)) >= 2.4:
            reason = "POSTERIOR_THRESHOLD"
            break
    loss = sum(likelihood_rows)
    credit = 1.0 if (loss > 0 and event["secret"] == 1) or (loss < 0 and event["secret"] == 0) else 0.5
    return {"pair_id": event["pair_id"], "secret": event["secret"], "policy": policy,
            "task_ready": event["task_ready"], "public_predicate_released": True,
            "task_completed": bool(event["task_ready"]), "routes": channel_rows,
            "responses": history, "epsilon_increments": [EPS[x] for x in channel_rows],
            "llr_increments": likelihood_rows, "composed_epsilon": round(total, 12),
            "odometer_visible": policy in ("SYMBOLIC_ODOMETER", "ADAPTIVE_EPSILON_FILTER"),
            "accounting_decisions": accounting_decisions,
            "privacy_loss_llr": round(loss, 12), "filter_rejected_next_query": refused,
            "stop_reason": reason, "distinguisher_credit": credit}


def validate(inputs, outputs):
    errors = []
    paired = defaultdict(list)
    for event in inputs:
        if event["secret"] not in (0, 1) or len(event["uniforms"]) != 8 or any(not 0 <= x < 1 for x in event["uniforms"]):
            errors.append(f"invalid-input:{event.get('pair_id')}:{event.get('secret')}")
        paired[event["pair_id"]].append(event)
    for pair, members in paired.items():
        if len(members) != 2 or {x["secret"] for x in members} != {0, 1}:
            errors.append(f"invalid-neighbor-pair:{pair}")
        elif members[0]["task_ready"] != members[1]["task_ready"] or members[0]["uniforms"] != members[1]["uniforms"]:
            errors.append(f"neighbor-differs-beyond-secret:{pair}")
    index = {}
    for row in outputs:
        key = (row["pair_id"], row["secret"], row["policy"])
        if key in index:
            errors.append(f"duplicate-row:{key}")
        index[key] = row
    expected_keys = set()
    for event in inputs:
        for policy in NAMES:
            key = (event["pair_id"], event["secret"], policy)
            expected_keys.add(key)
            actual = index.get(key)
            if actual != reconstruct(event, policy):
                errors.append(f"row-mismatch:{key}")
    if set(index) != expected_keys:
        errors.append("row-key-set-mismatch")
    return errors


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["policy"]].append(row)
    table = []
    for name in NAMES:
        group = grouped[name]
        values = [x["composed_epsilon"] for x in group]
        table.append({"policy": name, "episodes": len(group), "pairs": len(group) // 2,
                      "secret_queries": sum(len(x["routes"]) for x in group),
                      "mean_queries": round(sum(len(x["routes"]) for x in group) / len(group), 6),
                      "max_queries": max(len(x["routes"]) for x in group),
                      "max_composed_epsilon": max(values),
                      "mean_composed_epsilon": round(sum(values) / len(values), 6),
                      "episodes_over_1_2": sum(x > 1.2 + 1e-12 for x in values),
                      "filter_rejections": sum(x["filter_rejected_next_query"] for x in group),
                      "max_abs_llr": max(abs(x["privacy_loss_llr"]) for x in group),
                      "distinguisher_accuracy": round(sum(x["distinguisher_credit"] for x in group) / len(group), 6),
                      "task_completions": sum(x["task_completed"] for x in group),
                      "task_ready": sum(x["task_ready"] for x in group),
                      "predicate_releases": sum(x["public_predicate_released"] for x in group)})
    return table


def preregistered_gate_errors(inputs, outputs):
    errors = []
    if len(inputs) != 4096:
        errors.append("input-episode-count")
    stats = {row["policy"]: row for row in summarize(outputs)}
    for policy in ("STATIC_PER_CALL", "GLOBAL_QUERY_CAP", "SYMBOLIC_ODOMETER"):
        if stats[policy]["episodes_over_1_2"] == 0:
            errors.append(f"no-composition-over-budget:{policy}")
    filt = [r for r in outputs if r["policy"] == "ADAPTIVE_EPSILON_FILTER"]
    if not filt or any(r["composed_epsilon"] > 1.2 + 1e-12 for r in filt):
        errors.append("adaptive-filter-budget-exceeded")
    if stats["ADAPTIVE_EPSILON_FILTER"]["filter_rejections"] == 0:
        errors.append("adaptive-filter-never-refused")
    predicate = stats["PREDICATE_ONLY"]
    if predicate["max_queries"] != 0 or predicate["distinguisher_accuracy"] != 0.5:
        errors.append("predicate-only-leaks-secret")
    completions = {v["task_completions"] for v in stats.values()}
    if len(completions) != 1 or predicate["predicate_releases"] != len(inputs):
        errors.append("public-predicate-utility-mismatch")
    for row in outputs:
        if abs(row["privacy_loss_llr"]) > row["composed_epsilon"] + 1e-9:
            errors.append("realized-likelihood-loss-exceeds-composed-epsilon")
            break
        if row["policy"] in ("SYMBOLIC_ODOMETER", "ADAPTIVE_EPSILON_FILTER"):
            expected_entries = len(row["routes"]) + int(row["filter_rejected_next_query"])
            if len(row["accounting_decisions"]) != expected_entries:
                errors.append("odometer-decision-log-incomplete")
                break
    return errors


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def main():
    root = Path(sys.argv[1])
    inpath, outpath, sumpath = root / "inputs.jsonl", root / "outcomes.jsonl", root / "summary.json"
    inputs, outputs = read_jsonl(inpath), read_jsonl(outpath)
    summary = json.loads(sumpath.read_text())
    errors = validate(inputs, outputs)
    errors.extend(preregistered_gate_errors(inputs, outputs))
    if summary.get("groups") != summarize(outputs):
        errors.append("summary-replay-mismatch")
    if summary.get("episodes") != len(inputs) or summary.get("outcome_rows") != len(outputs):
        errors.append("summary-count-mismatch")
    controls = []
    for field, changed in (("composed_epsilon", 99.0), ("task_completed", not outputs[0]["task_completed"]),
                           ("privacy_loss_llr", 99.0)):
        altered = deepcopy(outputs)
        altered[0][field] = changed
        controls.append(bool(validate(inputs, altered)))
    controls.append(bool(validate(inputs, outputs[:-1])))
    filt = [r for r in outputs if r["policy"] == "ADAPTIVE_EPSILON_FILTER"]
    predicate = [r for r in outputs if r["policy"] == "PREDICATE_ONLY"]
    result = {"status": "PASS_RAW_AUDIT" if not errors and sum(controls) == 4 and
              all(r["composed_epsilon"] <= 1.2 + 1e-12 for r in filt) and
              all(not r["routes"] and r["privacy_loss_llr"] == 0 for r in predicate) else "FAIL_RAW_AUDIT",
              "input_rows": len(inputs), "outcome_rows": len(outputs), "errors": errors[:20],
              "mutation_controls_rejected": sum(controls), "mutation_controls_total": 4,
              "inputs_sha256": hashlib.sha256(inpath.read_bytes()).hexdigest(),
              "outcomes_sha256": hashlib.sha256(outpath.read_bytes()).hexdigest(),
              "summary_sha256": hashlib.sha256(sumpath.read_bytes()).hexdigest()}
    (root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_RAW_AUDIT" else 1)


if __name__ == "__main__":
    main()
