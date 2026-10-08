import json
import sys
from collections import defaultdict
from pathlib import Path


POLICIES = ("cost_only", "entropy_threshold", "decision_value", "oracle_best_check")


def score(model, key, raw):
    models = {case["case_id"]: case for case in model["cases"]}
    raw_cases = {case["case_id"]: case for case in raw["cases"]}
    rows = []
    grouped = defaultdict(list)
    for world_index, world in enumerate(key["worlds"]):
        case = models[world["case_id"]]
        state = next((s for s in case["states"] if s["id"] == world["true_state"]), None)
        raw_case = raw_cases[world["case_id"]]
        for policy_name in POLICIES:
            policy = raw_case["policies"][policy_name]
            selected = policy["selected_check"]
            if policy["disposition"] == "UNKNOWN" or state is None:
                signal = "__UNKNOWN__"
                action = "YIELD"
                cost = 0.0
                regret = None
                status = "UNKNOWN"
            else:
                signal = state["signals"].get(selected, "__NO_CHECK__") if selected else "__NO_CHECK__"
                action = policy["routes_by_outcome"].get(signal, "YIELD")
                check = next((c for c in case["checks"] if c["id"] == selected), None) if selected else None
                cost = check["cost"] if check else 0.0
                status = "DECIDE" if action in case["routes"] else "UNKNOWN"
                regret = (
                    state["losses"][action] - min(state["losses"][route] for route in case["routes"])
                    if status == "DECIDE"
                    else None
                )
            row = {
                "world_index": world_index,
                "case_id": world["case_id"],
                "true_state": world["true_state"],
                "policy": policy_name,
                "signal": signal,
                "action": action,
                "status": status,
                "regret": regret,
                "check_cost": cost,
            }
            rows.append(row)
            grouped[(world["case_id"], policy_name)].append(row)

    summary = {}
    for case_id in models:
        case = models[case_id]
        summary[case_id] = {}
        for policy_name in POLICIES:
            group = grouped[(case_id, policy_name)]
            scored = [row for row in group if row["regret"] is not None]
            n = len(scored)
            mean_regret = sum(row["regret"] for row in scored) / n if n else None
            mean_cost = sum(row["check_cost"] for row in group) / len(group) if group else 0.0
            summary[case_id][policy_name] = {
                "worlds": len(group),
                "decisions": n,
                "yields": len(group) - n,
                "mean_regret": round(mean_regret, 12) if mean_regret is not None else None,
                "mean_check_cost": round(mean_cost, 12),
                "mean_regret_plus_cost": round(mean_regret + mean_cost, 12) if mean_regret is not None else None,
                "hard_gate_violations": sum(row["action"] not in case["routes"] and row["action"] != "YIELD" for row in group),
            }
    return {"schema": "decision-value-7934-score-v1", "rows": rows, "summary": summary}


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: scorer.py MODEL.json SCORING_KEY.json CANDIDATE.json OUTPUT.json")
    model, key, raw = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:4])
    output = score(model, key, raw)
    Path(argv[4]).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
