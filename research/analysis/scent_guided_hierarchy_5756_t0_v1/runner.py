"""One-shot paired T0 runner; hidden fixture oracle stays inside Environment."""

import argparse
import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

from candidate import POLICIES, run_policy


class Environment:
    def __init__(self, fixture, budget):
        self._fixture = fixture
        self._current = fixture["start"]
        self._budget = budget
        self._epoch = 0
        self._stack = []
        self._last_edges = None
        self._events = []
        self._cost = {"api_calls": 0, "observations": 0, "navigation": 0,
                      "backtracks": 0, "forbidden_effects": 0}

    def budget_remaining(self):
        return self._budget

    def _spend(self, kind):
        if self._budget <= 0:
            raise RuntimeError("budget exhausted")
        self._budget -= 1
        self._cost["api_calls"] += 1
        if kind in self._cost and kind != "api_calls":
            self._cost[kind] += 1

    def observe(self):
        self._spend("observations")
        node = self._fixture["screens"][self._current]
        observation = {"screen_id": self._current, "epoch": self._epoch,
                       "label": node["label"], "edges": [dict(edge) for edge in node["edges"]]}
        self._last_edges = {edge["id"]: edge for edge in observation["edges"]}
        self._events.append(copy.deepcopy({"kind": "OBSERVE", "observation": observation}))
        return copy.deepcopy(observation)

    def refuse(self, edge_id):
        edge = (self._last_edges or {}).get(edge_id)
        if edge is None or edge["reversible"]:
            raise RuntimeError("refusal must name a currently observed unsafe edge")
        self._spend("api_calls")
        event = {"kind": "REFUSE_UNSAFE", "screen_id": self._current, "edge_id": edge_id}
        self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)

    def navigate(self, edge_id):
        edge = (self._last_edges or {}).get(edge_id)
        if edge is None:
            raise RuntimeError("navigation edge was not in the latest observation")
        self._spend("navigation")
        if not edge["reversible"]:
            self._cost["forbidden_effects"] += 1
            event = {"kind": "FORBIDDEN_NAVIGATION", "screen_id": self._current, "edge_id": edge_id}
            self._events.append(copy.deepcopy(event))
            self._last_edges = None
            return copy.deepcopy(event)
        destination = self._fixture["transitions"][self._current][edge_id]
        source = self._current
        self._stack.append((source, edge_id, destination))
        self._current = destination
        self._last_edges = None
        event = {"kind": "NAVIGATE", "screen_id": source, "edge_id": edge_id, "to_screen": destination}
        self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)

    def backtrack(self):
        if not self._stack:
            raise RuntimeError("cannot backtrack from start")
        self._spend("backtracks")
        source, edge_id, current = self._stack.pop()
        if current != self._current:
            raise RuntimeError("navigation stack mismatch")
        self._current = source
        self._epoch = self._fixture.get("epoch_after_backtrack", {}).get(source, self._epoch)
        self._last_edges = None
        event = {"kind": "BACKTRACK", "from_screen": current, "to_screen": source,
                 "via_edge_id": edge_id, "epoch": self._epoch}
        self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)

    def record(self):
        return {"events": self._events, "cost": self._cost,
                "budget_remaining": self._budget, "final_screen": self._current}


def run(spec):
    results = []
    for fixture in spec["fixtures"]:
        for policy in POLICIES:
            env = Environment(fixture, spec["budget"])
            result = run_policy(env, spec["task"], policy)
            record = env.record()
            if fixture["target"] is None:
                eligibility = "NO_TARGET_CASE"
            elif not _safe_reachable(fixture):
                eligibility = "NO_SAFE_PATH"
            elif policy == "direct_search" and not fixture["direct_search"]:
                eligibility = "NOT_APPLICABLE_DIRECT_SEARCH_UNAVAILABLE"
            else:
                eligibility = "ELIGIBLE"
            results.append({"fixture_id": fixture["id"], "policy": policy,
                            "claim": result["claim"], "trace": result["trace"],
                            "environment_events": record["events"],
                            "cost": record["cost"], "budget_remaining": record["budget_remaining"],
                            "final_screen": record["final_screen"], "eligibility": eligibility})
    return results


def _safe_reachable(fixture):
    frontier = [fixture["start"]]
    seen = set()
    while frontier:
        node = frontier.pop()
        if node == fixture["target"]:
            return True
        if node in seen:
            continue
        seen.add(node)
        for edge in fixture["screens"][node]["edges"]:
            if edge["reversible"]:
                destination = fixture["transitions"].get(node, {}).get(edge["id"])
                if destination is not None:
                    frontier.append(destination)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    spec_bytes = (root / "spec.json").read_bytes()
    spec = json.loads(spec_bytes)
    results = run(spec)
    output = {"protocol": spec["protocol"],
              "runtime": {"python": sys.version, "platform": platform.platform(), "gpu": False},
              "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
              "result_count": len(results), "results": results}
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"protocol": output["protocol"], "spec_sha256": output["spec_sha256"],
                      "result_count": output["result_count"], "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()

