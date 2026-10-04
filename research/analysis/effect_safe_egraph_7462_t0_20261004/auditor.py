#!/usr/bin/env python3
"""Independent exhaustive transition/effect auditor for Issue #7462 T0."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULE_ORDER = ("deduplicate_passive_check", "idempotent_trim", "idempotent_lower", "commute_trim_lower")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def cost_vector(program, weights):
    ops = []
    node = program["pure_expr"]
    while isinstance(node, list) and len(node) == 2:
        ops.append(node[0])
        node = node[1]
    ops.extend(step["op"] for path in program["paths"].values() for step in path)
    return (sum(weights.get(op, 0) for op in ops), sum(weights.get(op, 0) > 0 for op in ops))


def independent_rewrites(program):
    """Separately authored finite rewrite relation for closure/baseline audit."""
    out = []

    def walk(expr):
        if not isinstance(expr, list) or len(expr) != 2:
            return []
        outer, inner = expr
        found = []
        for name, child in walk(inner):
            found.append((name, [outer, child]))
        if isinstance(inner, list) and len(inner) == 2:
            middle, leaf = inner
            if outer == middle == "TRIM":
                found.append(("idempotent_trim", [outer, leaf]))
            if outer == middle == "LOWER":
                found.append(("idempotent_lower", [outer, leaf]))
            if (outer, middle) in (("TRIM", "LOWER"), ("LOWER", "TRIM")):
                found.append(("commute_trim_lower", [middle, [outer, leaf]]))
        return found

    for name, expr in walk(program["pure_expr"]):
        changed = copy.deepcopy(program)
        changed["pure_expr"] = expr
        out.append((name, changed))
    for label, path in program["paths"].items():
        for pos in range(1, len(path)):
            if path[pos - 1] == path[pos] and path[pos].get("op") == "PASSIVE_CHECK":
                changed = copy.deepcopy(program)
                changed["paths"][label].pop(pos)
                out.append(("deduplicate_passive_check", changed))
    return [(name, value) for name, value in out if canonical(value) != canonical(program)]


def independent_greedy(source, weights):
    current = copy.deepcopy(source)
    while True:
        next_value = None
        for rule in RULE_ORDER:
            for name, value in sorted(independent_rewrites(current), key=lambda pair: (pair[0], canonical(pair[1]))):
                if name == rule and cost_vector(value, weights) < cost_vector(current, weights):
                    next_value = value
                    break
            if next_value is not None:
                break
        if next_value is None:
            return current
        current = next_value


def independent_closure(source, max_terms, max_rounds):
    source_key = canonical(source)
    terms = {source_key: source}
    frontier = [source_key]
    rounds = 0
    while frontier:
        if rounds >= max_rounds:
            return terms, False
        rounds += 1
        next_frontier = []
        for key in frontier:
            for _, value in independent_rewrites(terms[key]):
                new_key = canonical(value)
                if new_key in terms:
                    continue
                if len(terms) >= max_terms:
                    return terms, False
                terms[new_key] = value
                next_frontier.append(new_key)
        frontier = next_frontier
    return terms, True


def eval_expr(expr, text):
    if expr == ["INPUT"]:
        return text
    op, child = expr
    value = eval_expr(child, text)
    if op == "TRIM":
        return value.strip(" \t\n")
    if op == "LOWER":
        return value.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))
    raise ValueError(f"unknown pure op {op}")


def execute(program, path_name, steps, input_text, persisted, world_epoch, observed_epoch):
    value = eval_expr(program["pure_expr"], input_text)
    state = {"buffer": "unchanged", "persisted": persisted,
             "world_epoch": world_epoch, "observed_epoch": observed_epoch,
             "authority_held": True, "fresh_ok": None, "blocked": False,
             "events": [], "terminal": None, "hard_violations": []}
    for step in steps:
        op = step["op"]
        if op == "PASSIVE_CHECK":
            continue
        if op == "WORLD_CHANGE":
            state["world_epoch"] += 1
            state["events"].append({"effect": "WORLD_CHANGE", "epoch": state["world_epoch"]})
        elif op == "REFRESH":
            state["observed_epoch"] = state["world_epoch"]
            state["events"].append({"effect": "REFRESH", "source_epoch": state["observed_epoch"]})
        elif op == "CHECK_FRESH":
            state["fresh_ok"] = state["observed_epoch"] == state["world_epoch"]
            if not state["fresh_ok"]:
                state["blocked"] = True
                state["terminal"] = "HOLD_STALE_INPUT"
        elif op == "EDIT":
            if state["blocked"] or state["authority_held"] is False:
                state["hard_violations"].append("EDIT_WITHOUT_FRESH_AUTHORITY")
            else:
                state["buffer"] = value
                state["events"].append({"effect": "EDIT", "value": value})
        elif op == "SAVE":
            if state["blocked"] or state["authority_held"] is False:
                state["hard_violations"].append("SAVE_WITHOUT_FRESH_AUTHORITY")
            else:
                state["persisted"] = state["buffer"]
                state["events"].append({"effect": "SAVE", "value": state["persisted"]})
        elif op == "RELEASE":
            if state["authority_held"]:
                state["authority_held"] = False
                state["events"].append({"effect": "RELEASE"})
        elif op in ("RETURN_SUCCESS", "RETURN_UNKNOWN"):
            if state["authority_held"]:
                state["hard_violations"].append("AUTHORITY_HELD_AT_TERMINAL")
            if state["terminal"] is None:
                state["terminal"] = "SUCCESS" if op == "RETURN_SUCCESS" else "UNKNOWN"
        else:
            raise ValueError(f"unknown operation {op}")
    if state["terminal"] is None:
        state["terminal"] = "MISSING_TERMINAL"
        state["hard_violations"].append("MISSING_TERMINAL")
    return {"pure_value": value, "path": path_name,
            "events": state["events"], "buffer": state["buffer"],
            "persisted": state["persisted"], "world_epoch": state["world_epoch"],
            "observed_epoch": state["observed_epoch"],
            "authority_held": state["authority_held"],
            "terminal": state["terminal"],
            "hard_violations": state["hard_violations"]}


def scenarios(fixture):
    for input_text, persisted, epochs in itertools.product(
            fixture["inputs"], fixture["persisted_values"], fixture["starting_epochs"]):
        yield input_text, persisted, epochs[0], epochs[1]


def compare(fixture, source, candidate):
    errors = []
    count = 0
    for path_name, source_steps in source["paths"].items():
        candidate_steps = candidate["paths"].get(path_name)
        if candidate_steps is None:
            errors.append(f"missing path {path_name}")
            continue
        for inputs in scenarios(fixture):
            expected = execute(source, path_name, source_steps, *inputs)
            observed = execute(candidate, path_name, candidate_steps, *inputs)
            count += 1
            if observed != expected:
                errors.append(f"{source['program_id']}:{path_name} state={inputs!r} changed observable contract")
    if set(source["paths"]) != set(candidate["paths"]):
        errors.append(f"{source['program_id']}: path set changed")
    return errors, count


def corrupt(program, name):
    value = copy.deepcopy(program)
    steps = value["paths"]["known"]
    if name == "remove_refresh":
        index = next(i for i, step in enumerate(steps) if step["op"] == "REFRESH")
        del steps[index]
    elif name == "reorder_edit_save":
        edit = next(i for i, step in enumerate(steps) if step["op"] == "EDIT")
        save = next(i for i, step in enumerate(steps) if step["op"] == "SAVE")
        steps[edit], steps[save] = steps[save], steps[edit]
    elif name == "drop_release":
        index = next(i for i, step in enumerate(steps) if step["op"] == "RELEASE")
        del steps[index]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    fixture_digest = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
    candidate_digest = hashlib.sha256((HERE / "candidate.py").read_bytes()).hexdigest()
    source_by_id = {p["program_id"]: p for p in fixture["programs"]}
    raw_by_id = {r["program_id"]: r for r in raw.get("results", [])}
    errors, checked = [], 0
    if raw.get("fixture_sha256") != fixture_digest or raw.get("candidate_sha256") != candidate_digest:
        errors.append("raw fixture/candidate source digest mismatch")
    if len(raw.get("results", [])) != len(source_by_id) or set(raw_by_id) != set(source_by_id):
        errors.append("candidate program membership mismatch")
    for program_id, source in source_by_id.items():
        row = raw_by_id.get(program_id)
        if row is None:
            continue
        if row.get("source") != source:
            errors.append(f"{program_id}: source changed")
            continue
        expected_greedy = independent_greedy(source, fixture["cost_units"])
        if row.get("greedy") != expected_greedy:
            errors.append(f"{program_id}: fixed-order strict-improvement baseline mismatch")
        for label in ("greedy", "extracted"):
            observed = row.get(label)
            if not isinstance(observed, dict):
                errors.append(f"{program_id}: missing {label} program")
                continue
            mismatch, n = compare(fixture, source, observed)
            checked += n
            errors.extend(mismatch)
        stats = row.get("saturation", {})
        if stats.get("saturated") is not True or stats.get("extraction_failure") is not False:
            errors.append(f"{program_id}: incomplete equality closure/extraction")
        closure, closure_complete = independent_closure(
            source, fixture["limits"]["max_terms"], fixture["limits"]["max_rounds"])
        declared_keys = {canonical(term) for term in stats.get("saturated_terms", [])}
        if not closure_complete or declared_keys != set(closure):
            errors.append(f"{program_id}: saturated term closure mismatch/incomplete")
        expected_term_digest = hashlib.sha256("\n".join(sorted(closure)).encode()).hexdigest()
        if stats.get("term_count") != len(closure) or stats.get("term_set_sha256") != expected_term_digest:
            errors.append(f"{program_id}: term count/digest mismatch")
        best_key = min(closure, key=lambda key: (cost_vector(closure[key], fixture["cost_units"]), key))
        if row.get("extracted") != closure[best_key]:
            errors.append(f"{program_id}: extracted program is not minimum-cost closure member")
        if stats.get("selected_sha256") != hashlib.sha256(best_key.encode()).hexdigest():
            errors.append(f"{program_id}: selected-term digest mismatch")
        for label in ("source", "greedy", "extracted"):
            if row.get(f"{label}_cost") != list(cost_vector(row[label], fixture["cost_units"])):
                errors.append(f"{program_id}: reported {label} cost mismatch")
        if stats.get("selected_cost") != list(cost_vector(row.get("extracted", source), fixture["cost_units"])):
            errors.append(f"{program_id}: extraction cost receipt mismatch")
    heldout = next(p for p in fixture["programs"] if p["split"] == "heldout")
    heldout_row = raw_by_id.get(heldout["program_id"], {})
    heldout_gain = (cost_vector(heldout_row.get("extracted", heldout), fixture["cost_units"])
                    < cost_vector(heldout_row.get("greedy", heldout), fixture["cost_units"]))
    if not heldout_gain:
        errors.append("held-out extracted cost is not lower than greedy")
    mutations = {}
    extracted = heldout_row.get("extracted", heldout)
    for name in ("remove_refresh", "reorder_edit_save", "drop_release"):
        invalid = corrupt(extracted, name)
        mismatch, n = compare(fixture, heldout, invalid)
        checked += n
        mutations[name] = {"rejected": bool(mismatch), "counterexample_count": len(mismatch)}
        if not mismatch:
            errors.append(f"unsound mutation certified: {name}")
    result = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "programs": len(source_by_id), "exhaustive_state_comparisons": checked,
              "heldout_strict_cost_gain": heldout_gain, "mutations": mutations,
              "errors": errors,
              "scope": "finite authored ASCII DSL and stipulated transition/effect oracle; no GUI/runtime/user claim"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
