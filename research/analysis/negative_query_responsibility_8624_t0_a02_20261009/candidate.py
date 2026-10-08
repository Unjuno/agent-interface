#!/usr/bin/env python3
"""Finite candidate for signed-fact causes in frozen stratified Boolean rules."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_case(case: dict, endpoint: str) -> list[str]:
    errors: list[str] = []
    universe = case.get("universe")
    observed = case.get("observed")
    rules = case.get("rules")
    if (not isinstance(universe, list) or not universe or
            any(type(item) is not str or not item for item in universe) or
            len(set(universe)) != len(universe)):
        return ["invalid_universe"]
    if not isinstance(observed, list) or any(item not in universe for item in observed):
        errors.append("invalid_observed_state")
    if not isinstance(rules, list):
        return errors + ["invalid_rules"]
    head_levels: dict[str, int] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            errors.append("rule_not_object")
            continue
        head = rule.get("head")
        level = rule.get("stratum")
        if type(head) is not str or not head or type(level) is not int or level < 1:
            errors.append("invalid_rule_head_or_stratum")
            continue
        prior = head_levels.setdefault(head, level)
        if prior != level:
            errors.append("head_has_multiple_strata")
        for polarity in ("positive", "negative"):
            body = rule.get(polarity)
            if (not isinstance(body, list) or
                    any(type(atom) is not str or not atom for atom in body) or
                    len(set(body)) != len(body)):
                errors.append("invalid_rule_body")
    if endpoint not in head_levels:
        errors.append("endpoint_not_derived")
    for rule in rules:
        if not isinstance(rule, dict) or type(rule.get("head")) is not str:
            continue
        head = rule["head"]
        level = head_levels.get(head, -1)
        for atom in rule.get("positive", []):
            source_level = 0 if atom in universe else head_levels.get(atom)
            if source_level is None:
                errors.append("unknown_positive_atom:" + atom)
            elif source_level > level:
                errors.append("positive_dependency_not_stratified:" + atom)
        for atom in rule.get("negative", []):
            source_level = 0 if atom in universe else head_levels.get(atom)
            if source_level is None:
                errors.append("unknown_negative_atom:" + atom)
            elif source_level >= level:
                errors.append("negative_dependency_not_stratified:" + atom)
    return sorted(set(errors))


def evaluate(case: dict, endpoint: str, state: set[str]) -> int:
    rules = case["rules"]
    levels = sorted({rule["stratum"] for rule in rules})
    derived: set[str] = set()
    for level in levels:
        local = [rule for rule in rules if rule["stratum"] == level]
        while True:
            additions = {
                rule["head"] for rule in local
                if all(atom in state or atom in derived for atom in rule["positive"])
                and all(atom not in state and atom not in derived for atom in rule["negative"])
            }
            additions -= derived
            if not additions:
                break
            derived.update(additions)
    return int(endpoint in derived)


def assignment_for(mask: int, universe: list[str]) -> set[str]:
    return {name for index, name in enumerate(universe) if mask & (1 << index)}


def state_mask(state: set[str], universe: list[str]) -> int:
    return sum(1 << index for index, name in enumerate(universe) if name in state)


def subset(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    return all(a == b or a == -1 for a, b in zip(left, right))


def all_minimal_supports(truth: list[int], n: int) -> list[list[int]]:
    positive = [mask for mask, answer in enumerate(truth) if answer == 1]
    minimal = [mask for mask in positive if not any(
        other != mask and (other & mask) == other for other in positive)]
    return [list(i for i in range(n) if mask & (1 << i)) for mask in sorted(minimal)]


def all_minimal_flips(truth: list[int], observed_mask: int, n: int) -> list[list[int]]:
    observed = truth[observed_mask]
    changed: list[int] = []
    for delta in range(1 << n):
        if truth[observed_mask ^ delta] != observed:
            changed.append(delta)
    minimal = [delta for delta in changed if not any(
        other != delta and (other & delta) == other for other in changed)]
    return [list(i for i in range(n) if delta & (1 << i)) for delta in sorted(minimal)]


def cube_implies(pattern: tuple[int, ...], truth: list[int], outcome: int) -> bool:
    n = len(pattern)
    for mask in range(1 << n):
        if all(value == -1 or bool(mask & (1 << i)) == bool(value)
               for i, value in enumerate(pattern)):
            if truth[mask] != outcome:
                return False
    return True


def prime_cubes(truth: list[int], outcome: int, n: int) -> list[tuple[int, ...]]:
    result: list[tuple[int, ...]] = []
    for pattern in itertools.product((-1, 0, 1), repeat=n):
        if not cube_implies(pattern, truth, outcome):
            continue
        prime = True
        for index, value in enumerate(pattern):
            if value == -1:
                continue
            wider = list(pattern)
            wider[index] = -1
            if cube_implies(tuple(wider), truth, outcome):
                prime = False
                break
        if prime:
            result.append(pattern)
    return sorted(result)


def cube_literals(pattern: tuple[int, ...], universe: list[str]) -> list[str]:
    return [name if value == 1 else "!" + name
            for name, value in zip(universe, pattern) if value != -1]


def compatible_union(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...] | None:
    merged: list[int] = []
    for a, b in zip(left, right):
        if a != -1 and b != -1 and a != b:
            return None
        merged.append(a if a != -1 else b)
    return tuple(merged)


def responsibility_from_primes(
    current_primes: list[tuple[int, ...]],
    opposite_primes: list[tuple[int, ...]],
    observed: list[int],
    universe: list[str],
) -> dict[str, dict]:
    output: dict[str, dict] = {}
    n = len(universe)
    for candidate, name in enumerate(universe):
        minimum: int | None = None
        witnesses: set[tuple[int, ...]] = set()
        for current in current_primes:
            if current[candidate] != observed[candidate]:
                continue
            for opposite in opposite_primes:
                if opposite[candidate] != 1 - observed[candidate]:
                    continue
                adjusted = list(opposite)
                adjusted[candidate] = observed[candidate]
                merged = compatible_union(current, tuple(adjusted))
                if merged is None:
                    continue
                gamma = tuple(index for index, value in enumerate(merged)
                              if index != candidate and value != -1 and value != observed[index])
                size = len(gamma)
                if minimum is None or size < minimum:
                    minimum, witnesses = size, {gamma}
                elif size == minimum:
                    witnesses.add(gamma)
        if minimum is None:
            output[name] = {
                "current_literal": name if observed[candidate] else "!" + name,
                "actual_cause": False,
                "minimum_contingency_size": None,
                "minimum_contingencies": [],
                "responsibility": "0",
            }
        else:
            ordered = sorted(witnesses)
            output[name] = {
                "current_literal": name if observed[candidate] else "!" + name,
                "actual_cause": True,
                "minimum_contingency_size": minimum,
                "minimum_contingencies": [[universe[index] for index in gamma] for gamma in ordered],
                "responsibility": f"1/{minimum + 1}",
            }
    return output


def analyze_case(case: dict, endpoint: str, cube_scan_limit: int) -> dict:
    universe = case["universe"]
    n = len(universe)
    truth = [evaluate(case, endpoint, assignment_for(mask, universe))
             for mask in range(1 << n)]
    observed = [int(name in case["observed"]) for name in universe]
    observed_mask = state_mask(set(case["observed"]), universe)
    outcome = truth[observed_mask]
    flips = all_minimal_flips(truth, observed_mask, n)
    distances = [len(flip) for flip in flips]
    cube_count = 3 ** n
    common = {
        "case_id": case["id"],
        "role": case["role"],
        "outcome": outcome,
        "signed_facts": [
            {"fact": name, "present": bool(observed[index]),
             "literal": name if observed[index] else "!" + name}
            for index, name in enumerate(universe)],
        "minimal_positive_supports": all_minimal_supports(truth, n),
        "minimal_outcome_flip_sets": flips,
        "robustness_radius": min(distances) if distances else None,
        "truth_table_rows": 1 << n,
        "prime_cube_scan_bound": cube_count,
    }
    if cube_count > cube_scan_limit:
        common["prime_analysis"] = {
            "status": "UNKNOWN_TOO_LARGE",
            "limit": cube_scan_limit,
            "reason": "complete_cube_scan_bound_exceeds_frozen_budget",
            "current_outcome_terms": None,
            "opposite_outcome_terms": None,
            "causal_results": None,
        }
        return common
    current_primes = prime_cubes(truth, outcome, n)
    opposite_primes = prime_cubes(truth, 1 - outcome, n)
    common["prime_analysis"] = {
        "status": "COMPLETE",
        "limit": cube_scan_limit,
        "current_outcome_terms": sorted(cube_literals(term, universe) for term in current_primes),
        "opposite_outcome_terms": sorted(cube_literals(term, universe) for term in opposite_primes),
        "causal_results": responsibility_from_primes(
            current_primes, opposite_primes, observed, universe),
    }
    return common


def build_output(model: dict, freeze: dict, package: Path) -> dict:
    source_hashes = {
        "model.json": sha256(package / "model.json"),
        "candidate.py": sha256(package / "candidate.py"),
        "auditor.py": sha256(package / "auditor.py"),
    }
    errors = []
    if source_hashes != freeze.get("source_hashes"):
        errors.append("frozen_source_hash_mismatch")
    cases = []
    for case in model.get("cases", []):
        invalid = validate_case(case, model.get("query_endpoint"))
        if invalid:
            errors.append(case.get("id", "unknown") + ":" + ",".join(invalid))
            continue
        cases.append(analyze_case(case, model["query_endpoint"], freeze["cube_scan_limit"]))
    return {
        "schema": "negative-query-responsibility-candidate-v1",
        "allocation": freeze["allocation"],
        "main_sha": freeze["main_sha"],
        "status": "CANDIDATE_COMPLETE" if not errors else "CANDIDATE_STOP",
        "errors": errors,
        "source_hashes": source_hashes,
        "case_count": len(cases),
        "cases": cases,
    }


def main() -> int:
    package = Path(__file__).resolve().parent
    model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else package / "model.json"
    freeze_path = Path(sys.argv[2]) if len(sys.argv) > 2 else package / "FREEZE.json"
    model = json.loads(model_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    output = build_output(model, freeze, package)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if output["status"] == "CANDIDATE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
