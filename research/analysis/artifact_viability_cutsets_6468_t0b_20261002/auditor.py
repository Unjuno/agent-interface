import copy
import hashlib
import itertools
import json
import pathlib
import re
import sys


def _strict(contract, outcomes):
    for key in contract["must_pass"]:
        if outcomes[key] == "FAIL":
            return "FAIL"
    if any(outcomes[key] == "UNKNOWN" for key in contract["must_pass"]):
        return "UNKNOWN"
    uncertain = False
    for group in contract["alternatives"]:
        group_values = [outcomes[key] for key in group]
        if all(value == "FAIL" for value in group_values):
            return "FAIL"
        if "PASS" not in group_values:
            uncertain = True
    return "UNKNOWN" if uncertain else "PASS"


def _cut_sets(contract):
    identifiers = sorted(contract["checks"])
    cuts = []
    for width in range(1, len(identifiers) + 1):
        for failed_tuple in itertools.combinations(identifiers, width):
            failed = set(failed_tuple)
            if any(set(prior).issubset(failed) for prior in cuts):
                continue
            outcomes = {key: ("FAIL" if key in failed else "PASS") for key in identifiers}
            if _strict(contract, outcomes) == "FAIL":
                cuts.append(list(failed_tuple))
    return cuts


def _dependency_status(contract, outcomes, cuts):
    unknown = [key for key, value in outcomes.items() if value == "UNKNOWN"]
    possibilities = set()
    for assignment in itertools.product(("PASS", "FAIL"), repeat=len(unknown)):
        resolved = dict(outcomes)
        resolved.update(zip(unknown, assignment))
        failed = {key for key, value in resolved.items() if value == "FAIL"}
        possibilities.add("FAIL" if any(set(cut) <= failed for cut in cuts) else "PASS")
    if possibilities == {"PASS"}:
        return "PASS"
    if possibilities == {"FAIL"}:
        return "FAIL"
    return "UNKNOWN"


def _validate_oracles(case, route_name, observations, evidence):
    problems = []
    if "claim_source_id" in evidence:
        expected = "PASS" if evidence.get("claim_source_id") == evidence.get("citation_target_id") else "FAIL"
        if observations.get("claim_citation_binding") != expected:
            problems.append(f"{case['case_id']}/{route_name}: citation-binding oracle mismatch")
    if "expected_formula" in evidence:
        actual = evidence.get("observed_formula")
        if observations.get("formula_correct") != ("PASS" if actual == evidence["expected_formula"] else "FAIL"):
            problems.append(f"{case['case_id']}/{route_name}: formula oracle mismatch")
        expected_range = re.search(r"\(([^()]*)\)", evidence["expected_formula"])
        actual_range = re.search(r"\(([^()]*)\)", actual or "")
        equal = bool(expected_range and actual_range and expected_range.group(1) == actual_range.group(1))
        if observations.get("formula_range_correct") != ("PASS" if equal else "FAIL"):
            problems.append(f"{case['case_id']}/{route_name}: formula-range oracle mismatch")
    return problems


def reconstruct(fixture):
    results = []
    all_problems = []
    for contract_name, contract in fixture["contracts"].items():
        identifiers = set(contract["checks"])
        if not 6 <= len(identifiers) <= 10:
            all_problems.append(f"{contract_name}: check count outside frozen 6-10 band")
        if not set(contract["must_pass"]).issubset(identifiers) or any(not set(group) <= identifiers for group in contract["alternatives"]):
            all_problems.append(f"{contract_name}: contract references unknown check")
        cuts = _cut_sets(contract)
        if not cuts:
            all_problems.append(f"{contract_name}: no minimal failure cut set")

    for case in fixture["cases"]:
        contract = fixture["contracts"][case["contract"]]
        route_results = {}
        for route_name, route in case["routes"].items():
            observations = route["observations"]
            if set(observations) != set(contract["checks"]):
                all_problems.append(f"{case['case_id']}/{route_name}: observation keys differ from contract")
                continue
            if any(value not in {"PASS", "FAIL", "UNKNOWN"} for value in observations.values()):
                all_problems.append(f"{case['case_id']}/{route_name}: invalid observation state")
                continue
            evidence = route.get("evidence", {})
            all_problems.extend(_validate_oracles(case, route_name, observations, evidence))
            strict_status = _strict(contract, observations)
            dependency_status = _dependency_status(contract, observations, _cut_sets(contract))
            failed = [key for key in contract["must_pass"] if observations[key] == "FAIL"]
            unknown = [key for key in contract["must_pass"] if observations[key] == "UNKNOWN"]
            for group in contract["alternatives"]:
                values = [observations[key] for key in group]
                label = "(" + " OR ".join(group) + ")"
                if "PASS" not in values:
                    (failed if all(value == "FAIL" for value in values) else unknown).append(label)
            route_results[route_name] = {
                "partial_score": sum(contract["checks"][key]["weight"] for key, value in observations.items() if value == "PASS"),
                "viability": dependency_status,
                "strict_status": strict_status,
                "dependency_status": dependency_status,
                "failed_gates": sorted(failed),
                "unknown_gates": sorted(unknown),
                "observations": observations,
                "evidence": evidence,
            }
        results.append({"case_id": case["case_id"], "contract": case["contract"], "routes": route_results})
    expected = {
        "schema": "artifact-viability-candidate-v1",
        "attempted_cases": len(fixture["cases"]),
        "minimal_cut_sets": {key: _cut_sets(value) for key, value in fixture["contracts"].items()},
        "results": results,
    }
    return expected, all_problems


def audit(fixture, candidate_result, expected_fixture_sha256=None):
    errors = []
    if expected_fixture_sha256 is not None:
        actual = hashlib.sha256(json.dumps(fixture, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        if actual != expected_fixture_sha256:
            errors.append("fixture canonical SHA-256 mismatch")
    expected, problems = reconstruct(fixture)
    errors.extend(problems)
    if candidate_result != expected:
        errors.append("raw candidate output differs from independent reconstruction")
    routes = [route for case in expected["results"] for route in case["routes"].values()]
    disagreement = sum(route["strict_status"] != route["dependency_status"] for route in routes)
    inversions = sum(case["routes"]["A"]["viability"] == "PASS" and case["routes"]["B"]["viability"] == "FAIL" and case["routes"]["B"]["partial_score"] >= case["routes"]["A"]["partial_score"] for case in expected["results"])
    return {"accepted": not errors, "audited_cases": len(expected["results"]), "audited_routes": len(routes),
            "strict_dependency_decision_disagreements": disagreement, "partial_score_inversions": inversions,
            "minimal_cut_sets": expected["minimal_cut_sets"], "errors": errors}


def _mutation_controls(fixture, raw, expected_fixture_sha256):
    controls = []
    mutations = [
        ("drop_critical_requirement", lambda value: value["results"][0]["routes"]["B"]["failed_gates"].remove("claim_citation_binding")),
        ("unknown_to_pass", lambda value: value["results"][4]["routes"]["B"].update({"viability": "PASS", "dependency_status": "PASS"})),
        ("swap_citation_target", lambda value: value["results"][0]["routes"]["A"]["evidence"].update({"citation_target_id": "study-2"})),
        ("double_count_checkpoint", lambda value: value["results"][0]["routes"]["A"].update({"partial_score": value["results"][0]["routes"]["A"]["partial_score"] + 3})),
        ("cosmetic_as_hard_gate", lambda value: value["results"][2]["routes"]["B"].update({"viability": "FAIL", "dependency_status": "FAIL"})),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls.append({"mutation": name, "rejected": not audit(fixture, changed, expected_fixture_sha256)["accepted"]})
    return controls


if __name__ == "__main__":
    fixture_path, raw_path, freeze_path, output_path = map(pathlib.Path, sys.argv[1:5])
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    result = audit(fixture, raw, freeze["fixture_canonical_sha256"])
    result["mutation_controls"] = _mutation_controls(fixture, raw, freeze["fixture_canonical_sha256"])
    result["all_mutations_rejected"] = all(item["rejected"] for item in result["mutation_controls"])
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("ACCEPTED" if result["accepted"] and result["all_mutations_rejected"] else "REJECTED")
    raise SystemExit(0 if result["accepted"] and result["all_mutations_rejected"] else 1)
