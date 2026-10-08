#!/usr/bin/env python3
"""Independent raw-only coalition and endpoint auditor."""
from __future__ import annotations

from fractions import Fraction
import itertools
import json
import sys
from pathlib import Path


TRUTH = {
    "additive_2f": ({"A", "B"}, {"-": 0, "A": 2, "B": 1, "AB": 3}, {"-", "A", "B", "AB"}),
    "positive_interaction_2f": ({"A", "B"}, {"-": 0, "A": 1, "B": 2, "AB": 5}, {"-", "A", "B", "AB"}),
    "negative_interaction_2f": ({"A", "B"}, {"-": 0, "A": 3, "B": 2, "AB": 4}, {"-", "A", "B", "AB"}),
    "three_factor_reversal": ({"A", "B", "C"}, {"-": 0, "A": 4, "B": 3, "C": 0, "AB": 7, "AC": 4, "BC": 10, "ABC": 11}, {"-", "A", "B", "C", "AB", "AC", "BC", "ABC"}),
    "infeasible_missing_B": ({"A", "B"}, {"-": 0, "A": 2, "AB": 4}, {"-", "A", "AB"}),
}


def fmt(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def exact_shapley(values: dict[str, Fraction], factors: set[str]) -> dict[str, str]:
    result = {}
    count = len(factors)
    for player in factors:
        others = factors - {player}
        total = Fraction(0)
        for size in range(len(others) + 1):
            for subset in itertools.combinations(sorted(others), size):
                left = "".join(sorted(subset)) or "-"
                right = "".join(sorted((*subset, player)))
                weight = Fraction(1, count * math_choose(count - 1, size))
                total += weight * (values[right] - values[left])
        result[player] = fmt(total)
    return result


def math_choose(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    out = 1
    for j in range(1, k + 1):
        out = out * (n - j + 1) // j
    return out


def audit_records(rows: list[dict]) -> dict:
    errors = []
    if len(rows) != len(TRUTH):
        errors.append("case_count")
    seen = set()
    total_arms = total_attempts = 0
    for row in rows:
        case = row.get("case_id")
        if case not in TRUTH or case in seen:
            errors.append(f"case_identity:{case}")
            continue
        seen.add(case)
        factors, expected_counts, feasible = TRUTH[case]
        if set(row.get("factors", [])) != factors:
            errors.append(f"factor_labels:{case}")
        arms = row.get("arms")
        if not isinstance(arms, list):
            errors.append(f"arms_type:{case}")
            continue
        coalition_rows = {}
        for arm in arms:
            key = arm.get("coalition")
            if key in coalition_rows:
                errors.append(f"duplicate_arm:{case}:{key}")
            coalition_rows[key] = arm
        total_arms += len(coalition_rows)
        if set(coalition_rows) != feasible:
            errors.append(f"feasible_arm_set:{case}")
        universe = {"".join(c) or "-" for n in range(len(factors) + 1) for c in itertools.combinations(sorted(factors), n)}
        missing = universe - feasible
        if set(row.get("infeasible_coalitions", [])) != missing:
            errors.append(f"infeasible_list:{case}")
        complete = not missing
        if row.get("disposition") != ("ANALYZE" if complete else "HOLD_NO_FEASIBLE_FACTORIAL"):
            errors.append(f"feasibility_disposition:{case}")
        if row.get("primary_characteristic") != "success_rate" or row.get("safety_scalarized") is not False:
            errors.append(f"endpoint_contract:{case}")
        if "utility" in row or "scalar_score" in row:
            errors.append(f"scalarized_endpoint_present:{case}")

        values: dict[str, Fraction] = {}
        safety, latency, tokens = {}, {}, {}
        for coalition in feasible:
            arm = coalition_rows.get(coalition)
            if not arm or arm.get("feasible") is not True:
                errors.append(f"arm_not_feasible:{case}:{coalition}")
                continue
            attempts = arm.get("attempts")
            if not isinstance(attempts, list) or len(attempts) != 20:
                errors.append(f"attempt_count:{case}:{coalition}")
                continue
            total_attempts += len(attempts)
            if [a.get("attempt") for a in attempts] != list(range(1, 21)):
                errors.append(f"attempt_identity:{case}:{coalition}")
            oracle = [a.get("oracle_effect") for a in attempts]
            reported = [a.get("reported_effect") for a in attempts]
            if oracle != reported:
                errors.append(f"effect_oracle_mismatch:{case}:{coalition}")
            if any(type(x) is not bool for x in oracle + reported):
                errors.append(f"effect_type:{case}:{coalition}")
            if sum(oracle) != expected_counts.get(coalition):
                errors.append(f"frozen_outcome_mismatch:{case}:{coalition}")
            for index, attempt in enumerate(attempts, start=1):
                expected_latency = 100 + 10 * len(coalition) + (index - 1) * 3
                expected_tokens = 20 + 2 * len(coalition) + (index - 1)
                if attempt.get("safety_events") != 0:
                    errors.append(f"safety_endpoint:{case}:{coalition}:{index}")
                if attempt.get("latency_ms") != expected_latency or attempt.get("tokens") != expected_tokens:
                    errors.append(f"frozen_cost_endpoint:{case}:{coalition}:{index}")
            values[coalition] = Fraction(sum(x is True for x in oracle), len(oracle))
            safety[coalition] = sum(a.get("safety_events", -999) for a in attempts)
            latency[coalition] = fmt(Fraction(sum(a.get("latency_ms", 0) for a in attempts), len(attempts)))
            tokens[coalition] = fmt(Fraction(sum(a.get("tokens", 0) for a in attempts), len(attempts)))
        want_metrics = {
            "success_rate": {k: fmt(v) for k, v in values.items()},
            "safety_events": safety,
            "mean_latency_ms": latency,
            "mean_tokens": tokens,
        }
        if row.get("metrics") != want_metrics:
            errors.append(f"endpoint_recompute:{case}")
        structurally_complete = complete and set(coalition_rows) == feasible and set(values) == feasible
        if structurally_complete:
            want_shapley = exact_shapley(values, factors)
            if row.get("shapley") != want_shapley:
                errors.append(f"shapley:{case}")
            if len(factors) == 2:
                a, b = sorted(factors)
                delta_shapley = Fraction(want_shapley[a]) - Fraction(want_shapley[b])
                delta_baseline = values[a] - values[b]
                if delta_shapley != delta_baseline:
                    errors.append(f"two_factor_rank_identity:{case}")
                expected_interaction = values["AB"] - values[a] - values[b] + values["-"]
                if row.get("interaction_2f") != fmt(expected_interaction):
                    errors.append(f"interaction_2f:{case}")
                if row.get("baseline_marginals") != {a: fmt(values[a] - values["-"]), b: fmt(values[b] - values["-"])}:
                    errors.append(f"baseline_marginals:{case}")
            else:
                if row.get("interaction_2f") is not None or row.get("baseline_marginals") is not None:
                    errors.append(f"three_factor_contrast_shape:{case}")
        else:
            if row.get("shapley") is not None or row.get("interaction_2f") is not None:
                errors.append(f"infeasible_allocation_not_held:{case}")
    if seen != set(TRUTH):
        errors.append("missing_case")
    three = next((r for r in rows if r.get("case_id") == "three_factor_reversal"), {})
    baseline = {k: TRUTH["three_factor_reversal"][1][k] for k in ("A", "B", "C")}
    base_reversal = baseline["A"] > baseline["B"]
    shap = three.get("shapley") or {}
    shap_reversal = Fraction(shap.get("A", "0")) < Fraction(shap.get("B", "0"))
    if not (base_reversal and shap_reversal):
        errors.append("three_factor_rank_reversal")
    return {
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "cases": len(rows),
        "feasible_arms": total_arms,
        "attempts": total_attempts,
        "three_factor_rank_reversal": base_reversal and shap_reversal,
        "infeasible_case_held": any(r.get("case_id") == "infeasible_missing_B" and r.get("disposition") == "HOLD_NO_FEASIBLE_FACTORIAL" for r in rows),
        "errors": errors,
    }


def main(path: str) -> int:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    result = audit_records(rows)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
