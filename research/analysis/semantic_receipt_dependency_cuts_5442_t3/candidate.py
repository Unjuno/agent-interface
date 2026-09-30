"""Finite synthetic observer-dependency simulation for Issue #5442 T3."""

import json


GOAL = "doc:v9"
PROVENANCE = {
    "observer_a": ["parser_a"],
    "parser_a": ["shared_cache"],
    "observer_b": ["parser_b"],
    "parser_b": ["shared_cache"],
    "observer_c": ["actuator_readback"],
    "shared_cache": ["semantic_state"],
    "actuator_readback": ["semantic_state"],
    "semantic_state": [],
}
FAULTABLE = ["parser_a", "parser_b", "shared_cache", "actuator_readback"]

SCENARIOS = [
    {"case_id": "no_fault", "failed": [], "actual": GOAL, "reports": {"observer_a": GOAL, "observer_b": GOAL, "observer_c": GOAL}},
    {"case_id": "parser_a_fault", "failed": ["parser_a"], "actual": GOAL, "reports": {"observer_a": "doc:v8", "observer_b": GOAL, "observer_c": GOAL}},
    {"case_id": "parser_b_fault", "failed": ["parser_b"], "actual": GOAL, "reports": {"observer_a": GOAL, "observer_b": "doc:v8", "observer_c": GOAL}},
    {"case_id": "shared_cache_common_lie", "failed": ["shared_cache"], "actual": "doc:v8", "reports": {"observer_a": GOAL, "observer_b": GOAL, "observer_c": "doc:v8"}},
    {"case_id": "actuator_readback_fault", "failed": ["actuator_readback"], "actual": GOAL, "reports": {"observer_a": GOAL, "observer_b": GOAL, "observer_c": "doc:v8"}},
]


def dependency_closure(graph, observer):
    reached, todo = set(), list(graph[observer])
    while todo:
        node = todo.pop()
        if node in reached:
            continue
        reached.add(node)
        todo.extend(graph[node])
    return reached


def evaluate(scenario):
    closures = {name: dependency_closure(PROVENANCE, name) & set(FAULTABLE) for name in PROVENANCE if name.startswith("observer_")}
    reports = scenario["reports"]
    failed = set(scenario["failed"])
    ab_agreement = reports["observer_a"] == reports["observer_b"] == GOAL
    healthy = [name for name in closures if not (closures[name] & failed)]
    excluded = sorted(set(closures) - set(healthy))
    independent_pairs = [
        [a, b]
        for i, a in enumerate(healthy)
        for b in healthy[i + 1:]
        if closures[a].isdisjoint(closures[b]) and reports[a] == GOAL and reports[b] == GOAL
    ]
    provenance_confirm = bool(independent_pairs)
    trusted_c_status = (
        "SEMANTICALLY_CONFIRMED" if reports["observer_c"] == GOAL else "SEMANTICALLY_CONTRADICTED"
    ) if "observer_c" in healthy else ("SEMANTICALLY_CONFIRMED" if provenance_confirm else "UNKNOWN")
    return {
        "dependency_closures": {name: sorted(items) for name, items in closures.items()},
        "ab_agreement_commit": ab_agreement,
        "provenance_pair_commit": provenance_confirm,
        "independent_pairs": independent_pairs,
        "excluded_observers": excluded,
        "trusted_c_status": trusted_c_status,
        "trusted_c_commit": trusted_c_status == "SEMANTICALLY_CONFIRMED",
    }


def run():
    for scenario in SCENARIOS:
        yield {
            "case_id": scenario["case_id"],
            "goal": GOAL,
            "actual": scenario["actual"],
            "provenance": PROVENANCE,
            "faultable_nodes": FAULTABLE,
            "failed_dependencies": scenario["failed"],
            "observer_reports": scenario["reports"],
            "trusted_endpoint": "observer_c",
            **evaluate(scenario),
        }


if __name__ == "__main__":
    for row in run():
        print(json.dumps(row, sort_keys=True, separators=(",", ":")))
