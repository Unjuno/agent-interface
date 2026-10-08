#!/usr/bin/env python3
"""Independent exact-rational audit of Issue #5444 T7 output."""
from fractions import Fraction
from itertools import product
import json
import sys


def expected_scenarios():
    rows = []
    for action in ("reversible", "irreversible"):
        for truth in ("safe", "unsafe"):
            for cost in range(5):
                for votes in product((0, 1), repeat=4):
                    score = sum((Fraction(2 * bit - 1) * Fraction(3, 40) for bit in votes), Fraction(0))
                    rows.append({
                        "scenario_id": f"{action}-{truth}-c{cost}-v{''.join(map(str, votes))}",
                        "action_class": action,
                        "oracle_truth": truth,
                        "compensation_cost": cost,
                        "authority_receipt": "UNKNOWN",
                        "low_verifier_votes": list(votes),
                        "low_verifier_score": float(score),
                        "vote_flips_to_unanimous_support": 4 - sum(votes),
                        "weighted_breakdown_flips_if_commit": 1 if score >= Fraction(3, 10) else None,
                    })
    return rows


def main(path):
    report = json.loads(open(path, encoding="utf-8").read())
    errors = []
    scenarios = expected_scenarios()
    if report.get("experiment") != "issue-5444-breakdown-t7-generated-family":
        errors.append("experiment identity mismatch")
    actual = report.get("scenarios", [])
    if actual != scenarios:
        errors.append("generated scenario rows mismatch independent rational construction")
    if report.get("scenario_count") != 320 or len(actual) != 320:
        errors.append("scenario coverage count mismatch")
    if len({row.get("scenario_id") for row in actual}) != 320:
        errors.append("scenario IDs are not unique")
    if [row.get("compensation_threshold") for row in report.get("sweep", [])] != list(range(5)):
        errors.append("threshold sweep coverage mismatch")

    for sweep in report.get("sweep", []):
        threshold = sweep["compensation_threshold"]
        for policy in ("UNKNOWN_FAIL_CLOSED", "UNKNOWN_AS_ZERO", "REVERSIBLE_COMPENSATION_FILTER"):
            decisions = []
            for row in scenarios:
                affirmative = Fraction(sum(2 * bit - 1 for bit in row["low_verifier_votes"]) * 3, 40) >= Fraction(3, 10)
                if policy == "UNKNOWN_FAIL_CLOSED":
                    commit = False
                elif policy == "UNKNOWN_AS_ZERO":
                    commit = affirmative
                else:
                    commit = affirmative and row["action_class"] == "reversible" and row["compensation_cost"] <= threshold
                decisions.append(commit)
            unsafe = sum(commit and row["oracle_truth"] == "unsafe" for commit, row in zip(decisions, scenarios))
            safe_total = sum(row["oracle_truth"] == "safe" for row in scenarios)
            safe_abstentions = sum((not commit) and row["oracle_truth"] == "safe" for commit, row in zip(decisions, scenarios))
            irreversible_unknown = sum(commit and row["action_class"] == "irreversible" for commit, row in zip(decisions, scenarios))
            expected = {
                "scenario_coverage": 320,
                "commits": sum(decisions),
                "commit_fraction_of_grid": sum(decisions) / 320,
                "unsafe_commits": unsafe,
                "unsafe_fraction_of_grid": unsafe / 320,
                "safe_abstentions": safe_abstentions,
                "safe_abstention_fraction": safe_abstentions / safe_total,
                "irreversible_unknown_commits": irreversible_unknown,
            }
            if sweep.get("policies", {}).get(policy) != expected:
                errors.append(f"threshold={threshold} {policy} aggregate mismatch")

    rows = report.get("sweep", [])
    filtered = [row["policies"]["REVERSIBLE_COMPENSATION_FILTER"] for row in rows]
    unsafe_counts = [row["unsafe_commits"] for row in filtered]
    if unsafe_counts != sorted(unsafe_counts) or unsafe_counts != [1, 2, 3, 4, 5]:
        errors.append("preregistered threshold/unsafe-commit Pareto discriminator mismatch")
    if any(row["irreversible_unknown_commits"] for row in filtered):
        errors.append("irreversible UNKNOWN commit detected")
    print(json.dumps({"audit": "PASS" if not errors else "FAIL", "errors": errors,
                      "scenario_rows_audited": len(actual), "thresholds_audited": len(rows),
                      "independent_exact_rational_reconstruction": True}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
