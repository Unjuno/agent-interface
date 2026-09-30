#!/usr/bin/env python3
"""Independent raw-output audit. Does not import candidate experiment functions."""
from fractions import Fraction
from itertools import product
import json
import sys


def main(path):
    report = json.loads(open(path, encoding="utf-8").read())
    errors = []
    if report.get("experiment") != "issue-5446-anytime-validity-t5":
        errors.append("experiment identity mismatch")
    if report.get("horizon") != 4 or report.get("branches") != 3 or report.get("threshold") != "2":
        errors.append("frozen parameter mismatch")
    expected_rhos = ["0/1", "1/4", "1/2", "1/1"]
    rows = report.get("rho_values", [])
    if [row.get("rho") for row in rows] != expected_rhos:
        errors.append("rho grid mismatch")

    for row in rows:
        rho = Fraction(row["rho"])
        masses = {}
        for bits in product((0, 1), repeat=3):
            common_mass = rho / 2 if len(set(bits)) == 1 else Fraction(0)
            masses[bits] = common_mass + (1 - rho) / 8
        outcomes = {k: Fraction(0) for k in (
            "fixed_A_anytime", "posthoc_max_branch_anytime", "fixed_equal_mixture_anytime",
            "predictable_adaptive_branch_anytime", "fixed_A_final_only",
        )}
        total = Fraction(0)
        for path in product(tuple(masses.items()), repeat=4):
            bits_path = tuple(item[0] for item in path)
            prob = Fraction(1)
            for bits, _ in path:
                prob *= masses[bits]
            if not prob:
                continue
            total += prob
            branch_wealth = [Fraction(1)] * 3
            branch_hits = [False] * 3
            mix_hit = adaptive_hit = False
            selected_branch = 0
            adaptive_wealth = Fraction(1)
            for time, bits in enumerate(bits_path):
                for branch, bit in enumerate(bits):
                    branch_wealth[branch] *= Fraction(3, 2) if bit else Fraction(1, 2)
                    branch_hits[branch] |= branch_wealth[branch] >= 2
                mix_hit |= sum(branch_wealth, Fraction(0)) / 3 >= 2
                selected_bit = bits[selected_branch]
                adaptive_wealth *= Fraction(3, 2) if selected_bit else Fraction(1, 2)
                adaptive_hit |= adaptive_wealth >= 2
                if time < 3:
                    selected_branch = (selected_branch + (1 if selected_bit else 2)) % 3
            outcomes["fixed_A_anytime"] += prob * branch_hits[0]
            outcomes["posthoc_max_branch_anytime"] += prob * any(branch_hits)
            outcomes["fixed_equal_mixture_anytime"] += prob * mix_hit
            outcomes["predictable_adaptive_branch_anytime"] += prob * adaptive_hit
            outcomes["fixed_A_final_only"] += prob * (branch_wealth[0] >= 2)
        if total != 1:
            errors.append(f"rho={rho}: probability mass {total}")
        # Fraction stringification canonicalizes one to "1", not "1/1".
        if Fraction(row.get("total_probability", "0")) != 1:
            errors.append(f"rho={rho}: reported total mass mismatch")
        for name, value in outcomes.items():
            if row["false_commit_probability"].get(name) != f"{value.numerator}/{value.denominator}":
                errors.append(f"rho={rho}: {name} exact fraction mismatch")
            reported = row["false_commit_decimal"].get(name)
            if reported is None or abs(reported - float(value)) > 1e-15:
                errors.append(f"rho={rho}: {name} decimal mismatch")

    # Mathematical and discriminator gates, checked independently from raw exact rates.
    for row in rows:
        values = {key: Fraction(value) for key, value in row["false_commit_probability"].items()}
        for valid in ("fixed_A_anytime", "fixed_equal_mixture_anytime", "predictable_adaptive_branch_anytime"):
            if values[valid] > Fraction(1, 2):
                errors.append(f"rho={row['rho']}: Ville bound exceeded by {valid}")
        if row["rho"] in ("0/1", "1/4") and values["posthoc_max_branch_anytime"] <= Fraction(1, 2):
            errors.append(f"rho={row['rho']}: preregistered post-hoc inflation discriminator absent")
    print(json.dumps({"audit": "PASS" if not errors else "FAIL", "errors": errors,
                      "rows_audited": len(rows), "independent_reimplementation": True}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
