"""Finite online route selector; costs are synthetic abstract units."""
import hashlib
import json
from pathlib import Path

ALLOCATION = "ROUTE-SWITCHING-6009-T0-20261001-01"
POLICIES = ("greedy", "sticky", "switch_aware")


def _eligible(task, routes):
    return [r for r in routes
            if task["eligible"].get(r) == "PASS"
            and task["proof"].get(r) == "PASS"]


def choose(policy, task, current, routes, transition):
    """Choose using one revealed task; future tasks are not an argument."""
    options = _eligible(task, routes)
    if not options:
        return None
    if policy == "greedy":
        return min(options, key=lambda r: (task["service"][r], r))
    if policy == "sticky":
        if current in options:
            return current
        if "A" in options:
            return "A"
        return min(options, key=lambda r: (task["service"][r], r))
    if policy == "switch_aware":
        def score(r):
            move = (transition["initial"][r] if current is None
                    else transition["between"][current][r])
            return move + task["service"][r], (r != current), r
        return min(options, key=score)
    raise ValueError("unknown policy")


def run(data):
    canon = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    output = {"schema":"route-switching-6009-candidate-v1",
              "allocation":ALLOCATION,
              "scenario_sha256":hashlib.sha256(canon).hexdigest(),"runs":[]}
    tr = data["transition"]
    for scenario in data["scenarios"]:
        for policy in POLICIES:
            route, spent, rows, stopped = None, 0, [], None
            for task in scenario["tasks"]:
                selected = choose(policy, task, route, data["routes"], tr)
                decision_cost = tr["decision_cost"]
                if selected is None:
                    spent += decision_cost
                    stopped = "NO_PROVEN_ROUTE"
                    rows.append({"task_id":task["id"],"status":"REFUSED",
                        "route":None,"proposed_route":None,"transition_cost":0,
                        "service_cost":0,"decision_cost":decision_cost,
                        "effect":None,"reason":stopped})
                    break
                move = tr["initial"][selected] if route is None else tr["between"][route][selected]
                service = task["service"][selected]
                if spent + decision_cost + move + service > scenario["deadline"]:
                    stopped = "DEADLINE_BEFORE_EFFECT"
                    spent += decision_cost
                    rows.append({"task_id":task["id"],"status":"REFUSED",
                        "route":None,"proposed_route":selected,
                        "transition_cost":0,"service_cost":0,
                        "proposed_transition_cost":move,"proposed_service_cost":service,
                        "decision_cost":decision_cost,"effect":None,"reason":stopped})
                    break
                rows.append({"task_id":task["id"],"status":"COMPLETED","route":selected,
                             "transition_cost":move,"service_cost":service,
                             "decision_cost":decision_cost,"effect":task["effect"]})
                spent += decision_cost + move + service
                route = selected
            complete = len(rows) == len(scenario["tasks"]) and all(
                row["status"] == "COMPLETED" for row in rows)
            terminal = tr["terminal_to_A"][route] if route else 0
            spent += terminal
            output["runs"].append({"scenario_id":scenario["id"],"policy":policy,
                "decisions":rows,"stopped":stopped,"terminal_cost":terminal,
                "total_cost":spent,"complete":complete,
                "deadline_met":spent <= scenario["deadline"],
                "effects":[row["effect"] for row in rows]})
    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", default=str(Path(__file__).with_name("scenarios.json")))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    Path(args.out).write_text(json.dumps(run(data), indent=2)+"\n", encoding="utf-8")
