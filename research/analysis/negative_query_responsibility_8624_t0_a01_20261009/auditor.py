#!/usr/bin/env python3
"""Independent intervention-enumeration auditor for the frozen T0 candidate."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_rules(case: dict, endpoint: str) -> list[str]:
    faults: set[str] = set()
    universe = case.get("universe")
    if not isinstance(universe, list) or len(set(universe)) != len(universe):
        return ["universe_invalid"]
    if any(type(fact) is not str or not fact for fact in universe):
        return ["universe_fact_invalid"]
    facts = set(universe)
    observed = case.get("observed")
    if not isinstance(observed, list) or not set(observed) <= facts:
        faults.add("observed_outside_mutable_universe")
    rules = case.get("rules")
    if not isinstance(rules, list):
        return sorted(faults | {"rules_not_list"})
    levels: dict[str, int] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            faults.add("rule_not_mapping")
            continue
        head, level = rule.get("head"), rule.get("stratum")
        if type(head) is not str or type(level) is not int or level < 1:
            faults.add("bad_head_or_level")
            continue
        if head in levels and levels[head] != level:
            faults.add("head_level_conflict")
        levels[head] = level
        for key in ("positive", "negative"):
            values = rule.get(key)
            if (not isinstance(values, list) or len(values) != len(set(values)) or
                    any(type(value) is not str or not value for value in values)):
                faults.add("bad_" + key + "_body")
    if endpoint not in levels:
        faults.add("query_endpoint_absent")
    for rule in rules:
        if not isinstance(rule, dict) or rule.get("head") not in levels:
            continue
        target_level = levels[rule["head"]]
        for atom in rule["positive"]:
            source_level = 0 if atom in facts else levels.get(atom)
            if source_level is None:
                faults.add("undefined_positive:" + atom)
            elif source_level > target_level:
                faults.add("positive_order_violation:" + atom)
        for atom in rule["negative"]:
            source_level = 0 if atom in facts else levels.get(atom)
            if source_level is None:
                faults.add("undefined_negative:" + atom)
            elif source_level >= target_level:
                faults.add("negative_order_violation:" + atom)
    return sorted(faults)


def program_answer(case: dict, endpoint: str, state_mask: int) -> int:
    universe = case["universe"]
    extensional = {fact for i, fact in enumerate(universe) if state_mask & (1 << i)}
    groups: dict[int, list[dict]] = {}
    for rule in case["rules"]:
        groups.setdefault(rule["stratum"], []).append(rule)
    intensional: set[str] = set()
    for level in sorted(groups):
        current = groups[level]
        while True:
            closure = set(intensional)
            for rule in current:
                if set(rule["positive"]) <= extensional | intensional and not (
                    set(rule["negative"]) & (extensional | intensional)
                ):
                    closure.add(rule["head"])
            delta = closure - intensional
            if not delta:
                break
            intensional.update(delta)
    return int(endpoint in intensional)


def qm_primes(truth: list[int], outcome: int, n: int) -> list[str]:
    terms = {
        "".join("1" if mask & (1 << index) else "0" for index in range(n))
        for mask, value in enumerate(truth) if value == outcome
    }
    prime_terms: set[str] = set()
    while terms:
        used: set[str] = set()
        next_terms: set[str] = set()
        ordered = sorted(terms)
        for left_index, left in enumerate(ordered):
            for right in ordered[left_index + 1:]:
                different = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
                if len(different) == 1 and left[different[0]] != "-" and right[different[0]] != "-":
                    position = different[0]
                    merged = left[:position] + "-" + left[position + 1:]
                    next_terms.add(merged)
                    used.add(left)
                    used.add(right)
        prime_terms.update(terms - used)
        terms = next_terms
    return sorted(prime_terms)


def literal_list(term: str, universe: list[str]) -> list[str]:
    return [name if bit == "1" else "!" + name
            for name, bit in zip(universe, term) if bit != "-"]


def direct_cause_oracle(truth: list[int], observed_mask: int, n: int) -> dict[str, dict]:
    outcome = truth[observed_mask]
    answer: dict[str, dict] = {}
    for candidate in range(n):
        minima: list[tuple[int, ...]] = []
        best: int | None = None
        for gamma_mask in range(1 << n):
            if gamma_mask & (1 << candidate):
                continue
            before = truth[observed_mask ^ gamma_mask]
            after = truth[observed_mask ^ gamma_mask ^ (1 << candidate)]
            if before == outcome and after == 1 - outcome:
                indices = tuple(i for i in range(n) if gamma_mask & (1 << i))
                if best is None or len(indices) < best:
                    best, minima = len(indices), [indices]
                elif len(indices) == best:
                    minima.append(indices)
        answer[str(candidate)] = {
            "actual_cause": best is not None,
            "minimum_contingency_size": best,
            "minimum_contingencies": [list(gamma) for gamma in sorted(minima)],
            "responsibility": "0" if best is None else f"1/{best + 1}",
        }
    return answer


def support_oracle(truth: list[int], n: int) -> list[list[int]]:
    winning = [state for state, value in enumerate(truth) if value]
    minimal = [state for state in winning if not any(
        other != state and (other & state) == other for other in winning)]
    return [[i for i in range(n) if state & (1 << i)] for state in sorted(minimal)]


def flip_oracle(truth: list[int], observed_mask: int, n: int) -> list[list[int]]:
    start = truth[observed_mask]
    changes = [delta for delta in range(1 << n)
               if truth[observed_mask ^ delta] != start]
    minima = [delta for delta in changes if not any(
        smaller != delta and (smaller & delta) == smaller for smaller in changes)]
    return [[i for i in range(n) if delta & (1 << i)] for delta in sorted(minima)]


def audit(model: dict, candidate: dict, freeze: dict, package: Path) -> dict:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    expected_hashes = {
        "model.json": digest(package / "model.json"),
        "candidate.py": digest(package / "candidate.py"),
        "auditor.py": digest(package / "auditor.py"),
    }
    checks["frozen_hashes_match"] = (
        expected_hashes == freeze.get("source_hashes") == candidate.get("source_hashes"))
    if not checks["frozen_hashes_match"]:
        errors.append("frozen_hash_mismatch")
    cases = model.get("cases")
    observed_results = candidate.get("cases")
    checks["candidate_completed"] = candidate.get("status") == "CANDIDATE_COMPLETE"
    checks["case_set_complete"] = (
        isinstance(cases, list) and isinstance(observed_results, list) and
        [case.get("id") for case in cases] == [row.get("case_id") for row in observed_results])
    if not checks["candidate_completed"]:
        errors.append("candidate_not_complete")
    if not checks["case_set_complete"]:
        errors.append("case_set_incomplete_or_reordered")
    if not checks["frozen_hashes_match"] or not checks["case_set_complete"]:
        return {"status": "FAIL", "checks": checks, "errors": errors,
                "case_count": 0, "assignment_rows": 0}

    rows = 0
    by_id: dict[str, dict] = {}
    for case, reported in zip(cases, observed_results):
        invalid = validate_rules(case, model["query_endpoint"])
        if invalid:
            errors.append(case["id"] + ":invalid_input:" + ",".join(invalid))
            continue
        universe = case["universe"]
        n = len(universe)
        truth = [program_answer(case, model["query_endpoint"], mask) for mask in range(1 << n)]
        rows += len(truth)
        observed_mask = sum(1 << i for i, fact in enumerate(universe) if fact in case["observed"])
        outcome = truth[observed_mask]
        support = support_oracle(truth, n)
        flips = flip_oracle(truth, observed_mask, n)
        radius = min(map(len, flips)) if flips else None
        oracle_causes = direct_cause_oracle(truth, observed_mask, n)
        prime_work = 3 ** n
        prime_report = reported.get("prime_analysis", {})
        local_checks = {
            "outcome": reported.get("outcome") == outcome,
            "truth_rows": reported.get("truth_table_rows") == len(truth),
            "supports": reported.get("minimal_positive_supports") == support,
            "minimal_flips": reported.get("minimal_outcome_flip_sets") == flips,
            "robustness": reported.get("robustness_radius") == radius,
        }
        if prime_work > freeze["cube_scan_limit"]:
            local_checks["complexity_unknown"] = (
                prime_report.get("status") == "UNKNOWN_TOO_LARGE" and
                prime_report.get("current_outcome_terms") is None and
                prime_report.get("opposite_outcome_terms") is None and
                prime_report.get("causal_results") is None and
                prime_report.get("limit") == freeze["cube_scan_limit"])
        else:
            prime_current = qm_primes(truth, outcome, n)
            prime_opposite = qm_primes(truth, 1 - outcome, n)
            current_lits = sorted(literal_list(term, universe) for term in prime_current)
            opposite_lits = sorted(literal_list(term, universe) for term in prime_opposite)
            prime_causes = prime_report.get("causal_results")
            local_checks["prime_family_status"] = prime_report.get("status") == "COMPLETE"
            local_checks["current_prime_terms"] = prime_report.get("current_outcome_terms") == current_lits
            local_checks["opposite_prime_terms"] = prime_report.get("opposite_outcome_terms") == opposite_lits
            local_checks["prime_causes_match_direct_oracle"] = isinstance(prime_causes, dict)
            if isinstance(prime_causes, dict):
                for index, fact in enumerate(universe):
                    actual = prime_causes.get(fact, {})
                    oracle = oracle_causes[str(index)]
                    mapped = {
                        "actual_cause": actual.get("actual_cause"),
                        "minimum_contingency_size": actual.get("minimum_contingency_size"),
                        "responsibility": actual.get("responsibility"),
                        "minimum_contingencies": sorted([
                            sorted(universe.index(name) for name in gamma)
                            for gamma in actual.get("minimum_contingencies", [])]),
                    }
                    expected = {
                        **oracle,
                        "minimum_contingencies": sorted(oracle["minimum_contingencies"]),
                    }
                    if mapped != expected:
                        local_checks["prime_causes_match_direct_oracle"] = False
                        errors.append(case["id"] + ":cause_mismatch:" + fact)
        checks[case["id"]] = all(local_checks.values())
        if not checks[case["id"]]:
            errors.append(case["id"] + ":" + ",".join(k for k, ok in local_checks.items() if not ok))
        by_id[case["id"]] = {
            "outcome": outcome,
            "supports": support,
            "minimal_flips": flips,
            "robustness_radius": radius,
            "causes": oracle_causes,
            "prime_terms": prime_report.get("status"),
        }

    if "same_support_flip_different_responsibility" in by_id and "same_support_flip_independent_response" in by_id:
        left = by_id["same_support_flip_different_responsibility"]
        right = by_id["same_support_flip_independent_response"]
        checks["paired_summaries_equal"] = (
            left["supports"] == right["supports"] and
            left["minimal_flips"] == right["minimal_flips"])
        checks["paired_responsibility_differs"] = (
            left["causes"]["1"]["actual_cause"] and
            left["causes"]["1"]["minimum_contingency_size"] == 2 and
            not right["causes"]["1"]["actual_cause"] and
            left["causes"]["2"]["actual_cause"] and
            not right["causes"]["2"]["actual_cause"])
    if "unit_robustness_large_named_contingency" in by_id:
        case = by_id["unit_robustness_large_named_contingency"]
        checks["radius_contingency_separation"] = (
            case["robustness_radius"] == 1 and
            case["causes"]["1"]["minimum_contingency_size"] == 3)
    dense = by_id.get("dense_parity_complexity_control")
    if dense:
        checks["dense_budget_refusal"] = (
            dense["prime_terms"] == "UNKNOWN_TOO_LARGE" and
            dense["robustness_radius"] == 1)
    checks["all_cases_exact"] = all(value for key, value in checks.items()
                                    if key not in {"all_cases_exact"})
    if not checks["all_cases_exact"]:
        errors.append("one_or_more_case_checks_failed")
    return {
        "status": "PASS_METHOD_SCOPED" if checks["all_cases_exact"] and not errors else "FAIL",
        "allocation": freeze["allocation"],
        "main_sha": freeze["main_sha"],
        "checks": checks,
        "errors": errors,
        "case_count": len(by_id),
        "assignment_rows": rows,
        "case_summary": by_id,
        "scope": "Finite authored stratified-rule fixtures only; no GUI, screenshot completeness, live causation, query freshness, action authority, production probability, or product benefit is tested.",
    }


def main() -> int:
    package = Path(__file__).resolve().parent
    model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else package / "model.json"
    raw_path = Path(sys.argv[2]) if len(sys.argv) > 2 else package / "results" / "candidate.raw.json"
    freeze_path = Path(sys.argv[3]) if len(sys.argv) > 3 else package / "FREEZE.json"
    model = json.loads(model_path.read_text())
    candidate = json.loads(raw_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    result = audit(model, candidate, freeze, package)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
