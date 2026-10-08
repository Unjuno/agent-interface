"""Independent exhaustive policy-tree checker; does not import candidate.py."""

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path


def canonical_digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _belief_key(values):
    return tuple(sorted(set(values)))


def _enumerate_policy_trees(case, belief, remaining):
    belief = _belief_key(belief)
    marker = set(case["marker"])
    unsafe = set(case["unsafe"])
    if set(belief) & unsafe:
        return []
    if set(belief) <= marker:
        return [{"terminal": "VERIFIED_MARKER"}]
    if remaining == 0:
        return []

    winners = []
    for action in sorted(case["authorized_actions"]):
        reached = set()
        usable = True
        for state in belief:
            outcomes = case["transitions"].get(state, {}).get(action, [])
            if not outcomes:
                usable = False
                break
            reached.update(outcomes)
        if not usable or reached & unsafe:
            continue

        observation_cells = {}
        for state in reached:
            label = case["observations"].get(state)
            if label is None:
                usable = False
                break
            observation_cells.setdefault(label, set()).add(state)
        if not usable:
            continue

        labels = sorted(observation_cells)
        branch_options = [
            _enumerate_policy_trees(case, observation_cells[label], remaining - 1)
            for label in labels
        ]
        if any(not options for options in branch_options):
            continue
        for selected in itertools.product(*branch_options):
            winners.append({
                "action": action,
                "branches": {label: tree for label, tree in zip(labels, selected)},
            })
    return winners


def _witness_is_valid(case, belief, remaining, policy):
    belief = _belief_key(belief)
    marker = set(case["marker"])
    unsafe = set(case["unsafe"])
    if set(belief) & unsafe:
        return False
    if set(belief) <= marker:
        return policy == {"terminal": "VERIFIED_MARKER"}
    if remaining == 0 or not isinstance(policy, dict):
        return False

    action = policy.get("action")
    if action not in case["authorized_actions"]:
        return False
    reached = set()
    for state in belief:
        outcomes = case["transitions"].get(state, {}).get(action, [])
        if not outcomes:
            return False
        reached.update(outcomes)
    if reached & unsafe:
        return False

    cells = {}
    for state in reached:
        label = case["observations"].get(state)
        if label is None:
            return False
        cells.setdefault(label, set()).add(state)
    branches = policy.get("branches")
    if not isinstance(branches, dict) or set(branches) != set(cells):
        return False
    return all(
        _witness_is_valid(case, cells[label], remaining - 1, branches[label])
        for label in cells
    )


def _expected(case, budget):
    if (
        not case.get("model_complete")
        or not case.get("transition_map_complete", True)
        or not case.get("generation_current")
        or not case.get("marker_verified")
    ):
        return {"status": "UNKNOWN", "minimum_steps": None, "margin": None}
    start = _belief_key(case["initial_belief"])
    for step_count in range(budget + 1):
        policies = _enumerate_policy_trees(case, start, step_count)
        if policies:
            return {
                "status": "RECOVERABLE",
                "minimum_steps": step_count,
                "margin": budget - step_count,
            }
    return {"status": "NOT_RECOVERABLE", "minimum_steps": None, "margin": None}


def _validate(fixture, raw, frozen_digest, truth):
    if canonical_digest(fixture) != frozen_digest:
        raise ValueError("fixture differs from frozen canonical digest")
    cases = {case["id"]: case for case in fixture["cases"]}
    wanted_count = len(cases) * len(fixture["horizons"])
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != wanted_count:
        raise ValueError("case-horizon row count mismatch")

    seen = set()
    for row in rows:
        case_id = row.get("case_id")
        horizon = row.get("horizon")
        key = (case_id, horizon)
        if key in seen or case_id not in cases or horizon not in fixture["horizons"]:
            raise ValueError("duplicate or undeclared row")
        seen.add(key)
        case = cases[case_id]
        budget = min(horizon, case.get("budget_cap", horizon))
        if row.get("effective_budget") != budget:
            raise ValueError("effective budget mismatch")
        expected = _expected(case, budget)
        expected_label = truth.get(case_id, {}).get(str(horizon))
        if expected_label != expected:
            raise ValueError("sealed expected label conflicts with independent enumeration")
        for field, value in expected.items():
            if row.get(field) != value:
                raise ValueError("result mismatch: " + repr((key, field)))
        if expected["status"] == "RECOVERABLE":
            if not _witness_is_valid(case, case["initial_belief"], budget, row.get("policy")):
                raise ValueError("invalid candidate witness")
        elif row.get("policy") is not None:
            raise ValueError("non-recoverable/unknown row carries a policy")

    expected_keys = {(case_id, h) for case_id in cases for h in fixture["horizons"]}
    if seen != expected_keys:
        raise ValueError("case-horizon coverage mismatch")

    control_case = next(c for c in fixture["cases"] if c["id"] == "aliased-opposite-actions")
    singleton_results = raw.get("singleton_controls")
    if not isinstance(singleton_results, list) or len(singleton_results) != 2:
        raise ValueError("singleton control count mismatch")
    for row in singleton_results:
        belief = row.get("belief")
        if belief not in control_case["singleton_controls"]:
            raise ValueError("unknown singleton control")
        expected = _expected({**control_case, "initial_belief": belief}, 2)
        result = row.get("result", {})
        for field, value in expected.items():
            if result.get(field) != value:
                raise ValueError("singleton result mismatch")
        if expected["status"] == "RECOVERABLE" and not _witness_is_valid(
            control_case, belief, 2, result.get("policy")
        ):
            raise ValueError("invalid singleton witness")
    return wanted_count


def audit(fixture, raw, frozen_digest, truth):
    row_count = _validate(fixture, raw, frozen_digest, truth)
    mutations = []

    dropped_state = copy.deepcopy(fixture)
    dropped_state["cases"][1]["initial_belief"] = ["L"]
    mutations.append(dropped_state)

    reclassified_event = copy.deepcopy(fixture)
    reclassified_event["cases"][4]["transitions"]["S"]["GO"] = ["M"]
    mutations.append(reclassified_event)

    moved_marker = copy.deepcopy(fixture)
    moved_marker["cases"][5]["marker"] = ["S0", "M"]
    mutations.append(moved_marker)

    rejected = 0
    for mutation in mutations:
        try:
            _validate(mutation, raw, frozen_digest, truth)
        except ValueError:
            rejected += 1
    if rejected != 3:
        raise ValueError("frozen-input mutation control missed")

    counts = {}
    for row in raw["rows"]:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "status": "PASS_BELIEF_RECOVERY_MARGIN_SCOPED",
        "rows": row_count,
        "status_counts": counts,
        "errors": [],
        "mutations_rejected": rejected,
        "aliased_singletons_recoverable_joint_not": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/input/input.json")
    parser.add_argument("--raw", default="/input/candidate.json")
    parser.add_argument("--freeze", default="/input/FREEZE.json")
    parser.add_argument("--truth", default="/input/truth.json")
    parser.add_argument("--output", default="/output/AUDIT.json")
    args = parser.parse_args()
    input_path = Path(args.input)
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    if hashlib.sha256(input_path.read_bytes()).hexdigest() != freeze["input_sha256"]:
        raise ValueError("input byte digest mismatch")
    truth_path = Path(args.truth)
    if hashlib.sha256(truth_path.read_bytes()).hexdigest() != freeze["truth_sha256"]:
        raise ValueError("truth byte digest mismatch")
    fixture = json.loads(input_path.read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    report = audit(fixture, raw, freeze["input_canonical_sha256"], truth)
    output = Path(args.output)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
