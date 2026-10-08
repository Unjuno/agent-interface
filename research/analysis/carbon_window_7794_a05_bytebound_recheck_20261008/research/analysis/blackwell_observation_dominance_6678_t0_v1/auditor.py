"""Independent exact Bayes-risk auditor for Issue #6678 T0."""

from fractions import Fraction
from itertools import product
import json
import sys


def frac(value):
    return Fraction(value[0], value[1]) if isinstance(value, list) else Fraction(value)


def risk(kernel, prior, losses):
    """Enumerate every deterministic output-to-action rule."""
    best = None
    for rule in product(range(len(losses[0])), repeat=len(kernel[0])):
        total = Fraction(0)
        for s, row in enumerate(kernel):
            for o, likelihood in enumerate(row):
                total += prior[s] * likelihood * losses[s][rule[o]]
        best = total if best is None or total < best else best
    return best


def parse_kernel(channel):
    return [[frac(x) for x in row] for row in channel["kernel"]]


def parse_prior(fixture):
    return [frac(x) for x in fixture["prior"]]


def independently_verify_certificate(source, target, encoded):
    if encoded is None:
        return False
    k = [[frac(x) for x in row] for row in encoded]
    if len(k) != len(source[0]) or any(len(row) != len(target[0]) for row in k):
        return False
    if any(sum(row) != 1 or any(x < 0 for x in row) for row in k):
        return False
    for s in range(len(source)):
        for j in range(len(target[0])):
            if sum(source[s][i] * k[i][j] for i in range(len(k))) != target[s][j]:
                return False
    return True


def audit(fixture, candidate):
    names = list(fixture["channels"])
    channels = {name: parse_kernel(fixture["channels"][name]) for name in names}
    prior = parse_prior(fixture)
    reports = candidate.get("relations")
    errors = []
    expected_labels = {f"{left}>={right}" for left in names for right in names}
    if not isinstance(reports, dict) or set(reports) != expected_labels:
        errors.append("candidate relation inventory mismatch")
    expected = fixture["expected_relations"]
    for label, expected_value in expected.items():
        left, right = label.split(">=")
        got = reports.get(label)
        if not isinstance(got, dict) or got.get("feasible") is not expected_value:
            errors.append("LP verdict mismatch: " + label)
            continue
        if expected_value and not independently_verify_certificate(
                channels[left], channels[right], got.get("garbling")):
            errors.append("invalid garbling certificate: " + label)
        if not expected_value and got.get("garbling") is not None:
            errors.append("unexpected certificate for infeasible control: " + label)

    risks = {}
    for pname, problem in fixture["decision_problems"].items():
        risks[pname] = {name: risk(channels[name], prior, problem["loss"]) for name in names}
    if not (risks["focus_s0"]["partition_s0"] < risks["focus_s0"]["partition_s2"]):
        errors.append("focus_s0 did not prefer partition_s0")
    if not (risks["focus_s2"]["partition_s2"] < risks["focus_s2"]["partition_s0"]):
        errors.append("focus_s2 did not prefer partition_s2")
    for pname, values in risks.items():
        if values["fine"] > values["partition_s0"] or values["fine"] > values["partition_s2"]:
            errors.append("fine channel risk exceeded a garbling: " + pname)
        if values["partition_s0"] > values["uninformative"] or values["partition_s2"] > values["uninformative"]:
            errors.append("partition risk exceeded its uninformative garbling: " + pname)
    for label, expected_value in expected.items():
        if expected_value:
            continue
        left, right = label.split(">=")
        if not any(values[left] > values[right] for values in risks.values()):
            errors.append("independent risk enumeration lacks non-dominance witness: " + label)
    if not (risks["exact_target"]["partition_s0"] > risks["exact_target"]["fine"]):
        errors.append("reverse fine/partition order lacks a strict risk witness")
    if not (risks["focus_s2"]["partition_s0"] > risks["focus_s2"]["partition_s2"] and
            risks["focus_s0"]["partition_s2"] > risks["focus_s0"]["partition_s0"]):
        errors.append("incomparable pair lacks opposing task-loss witnesses")
    if not (risks["focus_s0"]["uninformative"] > risks["focus_s0"]["partition_s0"]):
        errors.append("uninformative reverse-order control lacks a strict risk witness")

    # Relabel hidden states, actions, and channel outputs. With state/action
    # labels transported together, an arbitrary naming permutation must leave
    # the Bayes risk invariant.
    state_perm = fixture["relabel_permutation"]["states"]
    target_loss = fixture["decision_problems"]["exact_target"]["loss"]
    rel_prior = [prior[old] for old in state_perm]
    rel_loss = [[target_loss[old_s][old_a] for old_a in state_perm] +
                [target_loss[old_s][-1]] for old_s in state_perm]
    relabelled = []
    for old_s in state_perm:
        relabelled.append([channels["partition_s0"][old_s][old_o]
                           for old_o in fixture["relabel_permutation"]["partition_s0_outputs"]])
    relabelled_risk = risk(relabelled, rel_prior, rel_loss)
    if relabelled_risk != risks["exact_target"]["partition_s0"]:
        errors.append("hidden-state/action/output relabeling changed exact-target risk")

    # The candidate schema is intentionally observation-only: metadata that
    # leaks route identity into observation values is rejected by strict shape.
    if set(candidate) != {"schema", "relations", "observations"}:
        errors.append("candidate schema contains unexpected channel metadata")
    if candidate.get("schema") != "blackwell-candidate-v1":
        errors.append("candidate schema mismatch")
    expected_observations = [fixture["channels"][name]["outputs"] for name in names]
    if candidate.get("observations") != expected_observations:
        errors.append("observation payload leaked or changed channel identity/mapping")
    return {"verdict": "METHOD_PASS_SCOPED" if not errors else "FAIL_METHOD",
            "risks": {p: {n: [v.numerator, v.denominator] for n, v in vals.items()}
                      for p, vals in risks.items()},
            "relabelled_partition_s0_exact_target": [relabelled_risk.numerator, relabelled_risk.denominator],
            "errors": errors}


if __name__ == "__main__":
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    candidate = json.load(open(sys.argv[2], encoding="utf-8"))
    result = audit(fixture, candidate)
    json.dump(result, open(sys.argv[3], "w", encoding="utf-8"), sort_keys=True, indent=2)
    print(result["verdict"], "errors:", len(result["errors"]))
    raise SystemExit(bool(result["errors"]))
