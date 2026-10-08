#!/usr/bin/env python3
"""Independent exact-rational audit of the Issue #5428 T1 raw output."""
from fractions import Fraction as F
import json
import sys

LOSS = {"reversible": F(1, 4), "compensable": F(1, 2),
        "costly_to_reverse": F(1), "one_shot": F(2)}
PRIORS = {F(1, 10), F(1, 4), F(1, 2)}
ACCURACIES = {F(1, 2), F(3, 4), F(9, 10)}
WAIT_COSTS = {F(1, 4), F(3, 4)}
GOOD, ALT = F(2), F(3, 4)


def readq(obj):
    if not isinstance(obj, dict) or set(obj) != {"n", "d"}:
        raise ValueError("noncanonical rational")
    n, d = obj["n"], obj["d"]
    if not isinstance(n, int) or not isinstance(d, int) or d <= 0:
        raise ValueError("invalid rational components")
    q = F(n, d)
    if q.numerator != n or q.denominator != d:
        raise ValueError("unreduced rational")
    return q


def choose(primary, alternative):
    opts = [(F(0), "NOOP", 0)]
    if alternative:
        opts.append((ALT, "ALTERNATIVE", 1))
    if primary is not None:
        opts.append((primary, "PRIMARY", 2))
    value, action, _ = max(opts, key=lambda x: (x[0], -x[2]))
    return value, action


def primary(pbad, loss):
    return (1 - pbad) * GOOD - pbad * loss


def branch_values(pbad, accuracy, loss, alt_after, primary_after):
    expected_full = F(0)
    expected_primary = F(0)
    branch_rows = []
    for is_bad in (False, True):
        lb = accuracy if is_bad else 1 - accuracy
        lg = 1 - accuracy if is_bad else accuracy
        mass = pbad * lb + (1 - pbad) * lg
        if not mass:
            continue
        post = pbad * lb / mass
        pv = primary(post, loss) if primary_after else None
        vf, af = choose(pv, alt_after)
        vp, ap = choose(pv, False)
        expected_full += mass * vf
        expected_primary += mass * vp
        branch_rows.append(("bad" if is_bad else "good", mass, post, af, vf))
    return expected_full, expected_primary, branch_rows


def audit(report):
    errors = []
    if report.get("schema") != "issue-5428-real-option-t1-v1":
        errors.append("schema mismatch")
    rows = report.get("runs", [])
    expected = {
        (name, p, a, w, d, an, aa, ps, g)
        for name in LOSS for p in PRIORS for a in ACCURACIES for w in WAIT_COSTS
        for d in (False, True) for an in (False, True) for aa in (False, True)
        for ps in (False, True) for g in (False, True)
    }
    seen = set()
    high_rows = []
    for row in rows:
        try:
            key = (row["irreversibility"], readq(row["p_bad"]), readq(row["probe_accuracy"]),
                   readq(row["wait_cost"]), row["deadline_slack"], row["alternative_now"],
                   row["alternative_after"], row["primary_survives"], row["gate_open"])
            if key in seen:
                errors.append("duplicate factorial cell")
            seen.add(key)
            if key not in expected:
                errors.append("unexpected factorial cell")
                continue
            name, pbad, acc, wait, deadline, alt_now, alt_after, primary_after, gate = key
            loss = LOSS[name]
            current_primary = primary(pbad, loss) if gate else None
            immediate, immediate_action = choose(current_primary, gate and alt_now)
            full_probe, primary_probe, branches = branch_values(
                pbad, acc, loss, alt_after, primary_after) if gate and deadline else (None, None, [])
            reference = max(immediate, full_probe - wait if full_probe is not None else immediate)
            evsi = F(0)
            if gate:
                prior = max(F(0), primary(pbad, loss))
                posterior = F(0)
                for is_bad in (False, True):
                    lb = acc if is_bad else 1 - acc
                    lg = 1 - acc if is_bad else acc
                    mass = pbad * lb + (1 - pbad) * lg
                    if mass:
                        posterior += mass * max(F(0), primary(pbad * lb / mass, loss))
                evsi = posterior - prior

            expected_option_action = "WAIT_PROBE" if full_probe is not None and full_probe - wait > immediate else immediate_action
            option_value = full_probe - wait if expected_option_action == "WAIT_PROBE" else immediate
            if readq(row["reference_value"]) != reference:
                errors.append("reference value mismatch")
            if readq(row["evsi_primary_only"]) != evsi:
                errors.append("primary-only EVSI mismatch")
            no_alt = max(immediate, primary_probe - wait if primary_probe is not None else immediate)
            if readq(row["option_premium_vs_primary_only"]) != reference - no_alt:
                errors.append("route-option premium mismatch")
            safety = row["safety_only"]
            if safety["action"] != immediate_action or readq(safety["value"]) != immediate:
                errors.append("safety-only choice mismatch")
            if readq(safety["regret"]) != reference - immediate:
                errors.append("safety-only regret mismatch")
            voi_wait = full_probe is not None and evsi > wait
            voi_value = full_probe - wait if voi_wait else immediate
            voi_action = "WAIT_PROBE" if voi_wait else immediate_action
            voi = row["voi_only"]
            if voi["action"] != voi_action or readq(voi["value"]) != voi_value:
                errors.append("VOI-only choice mismatch")
            if readq(voi["regret"]) != reference - voi_value:
                errors.append("VOI-only regret mismatch")
            option = row["option_aware"]
            if option["action"] != expected_option_action or readq(option["value"]) != option_value:
                errors.append("option-aware choice mismatch")
            if readq(option["regret"]) != reference - option_value:
                errors.append("option-aware regret mismatch")
            deadline_loss = int(expected_option_action == "WAIT_PROBE" and not primary_after)
            if row["option_probe_induced_primary_deadline_loss"] != deadline_loss:
                errors.append("deadline-loss flag mismatch")
            if row["hard_gate_violations"] != 0:
                errors.append("hard-gate violation recorded")
            if name in ("costly_to_reverse", "one_shot"):
                high_rows.append(row)
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"malformed row: {type(exc).__name__}: {exc}")

    if len(rows) != 2304 or seen != expected:
        errors.append(f"factorial coverage mismatch: {len(rows)} rows / {len(seen)} unique")
    n = len(high_rows) or 1
    means = {policy: sum((readq(r[policy]["regret"]) for r in high_rows), F(0)) / n
             for policy in ("safety_only", "voi_only", "option_aware")}
    deadline_rate = F(sum(r["option_probe_induced_primary_deadline_loss"] for r in high_rows), n)
    gate_violations = sum(r["hard_gate_violations"] for r in rows)
    model_pass = (means["option_aware"] <= means["safety_only"] - F(1, 20)
                  and means["option_aware"] <= means["voi_only"] - F(1, 20)
                  and deadline_rate <= F(1, 20) and gate_violations == 0)
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "scenario_count": len(rows), "unique_cells": len(seen),
            "high_irreversibility_cases": len(high_rows),
            "mean_regret_high_irreversibility": {k: {"n": v.numerator, "d": v.denominator}
                                                for k, v in means.items()},
            "option_primary_deadline_loss_rate": {"n": deadline_rate.numerator, "d": deadline_rate.denominator},
            "hard_gate_violations": gate_violations,
            "preregistered_model_gate": "PASS" if model_pass and not errors else "FAIL",
            "runtime_transfer": "UNCERTAIN"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        print(json.dumps(audit(json.load(stream)), sort_keys=True, indent=2))
