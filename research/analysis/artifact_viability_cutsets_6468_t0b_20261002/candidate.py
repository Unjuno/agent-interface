import itertools
import json
import pathlib
import sys


def score_route(contract, observed):
    keys = set(contract["checks"])
    if set(observed) != keys or any(value not in {"PASS", "FAIL", "UNKNOWN"} for value in observed.values()):
        raise ValueError("observation vector does not match contract")
    referenced = set(contract["must_pass"]).union(*(set(group) for group in contract["alternatives"]))
    if not referenced.issubset(keys):
        raise ValueError("contract references an unknown check")
    score = sum(contract["checks"][key]["weight"] for key, value in observed.items() if value == "PASS")
    strict = _strict_status(contract, observed)
    cuts = minimal_cut_sets(contract)
    unknown_keys = sorted(key for key, value in observed.items() if value == "UNKNOWN")
    ledger_states = set()
    for completion in itertools.product(("PASS", "FAIL"), repeat=len(unknown_keys)):
        resolved = dict(observed)
        resolved.update(dict(zip(unknown_keys, completion)))
        failures = {key for key, value in resolved.items() if value == "FAIL"}
        ledger_states.add("FAIL" if any(set(cut).issubset(failures) for cut in cuts) else "PASS")
    dependency = ledger_states.pop() if len(ledger_states) == 1 else "UNKNOWN"
    failed = [key for key in contract["must_pass"] if observed[key] == "FAIL"]
    unknown = [key for key in contract["must_pass"] if observed[key] == "UNKNOWN"]
    for group in contract["alternatives"]:
        values = [observed[key] for key in group]
        label = "(" + " OR ".join(group) + ")"
        if "PASS" not in values:
            (failed if all(value == "FAIL" for value in values) else unknown).append(label)
    return {"partial_score": score, "viability": dependency, "strict_status": strict, "dependency_status": dependency,
            "failed_gates": sorted(failed), "unknown_gates": sorted(unknown)}


def _strict_status(contract, observed):
    if any(observed[key] == "FAIL" for key in contract["must_pass"]):
        return "FAIL"
    if any(observed[key] == "UNKNOWN" for key in contract["must_pass"]):
        return "UNKNOWN"
    unresolved = False
    for group in contract["alternatives"]:
        values = [observed[key] for key in group]
        if "PASS" not in values:
            if all(value == "FAIL" for value in values):
                return "FAIL"
            unresolved = True
    return "UNKNOWN" if unresolved else "PASS"


def minimal_cut_sets(contract):
    keys = sorted(contract["checks"])
    cuts = []
    for size in range(1, len(keys) + 1):
        for subset in itertools.combinations(keys, size):
            if any(set(previous).issubset(subset) for previous in cuts):
                continue
            observation = {key: ("FAIL" if key in subset else "PASS") for key in keys}
            if _strict_status(contract, observation) == "FAIL":
                cuts.append(list(subset))
    return cuts


def run(fixture):
    results = []
    for case in fixture["cases"]:
        contract = fixture["contracts"][case["contract"]]
        routes = {}
        for name, route in case["routes"].items():
            score = score_route(contract, route["observations"])
            routes[name] = {**score, "observations": route["observations"], "evidence": route.get("evidence", {})}
        results.append({"case_id": case["case_id"], "contract": case["contract"], "routes": routes})
    cuts = {name: minimal_cut_sets(contract) for name, contract in fixture["contracts"].items()}
    return {"schema": "artifact-viability-candidate-v1", "attempted_cases": len(results), "minimal_cut_sets": cuts, "results": results}


if __name__ == "__main__":
    source = pathlib.Path(sys.argv[1])
    target = pathlib.Path(sys.argv[2])
    target.write_text(json.dumps(run(json.loads(source.read_text())), sort_keys=True, indent=2) + "\n", encoding="utf-8")
