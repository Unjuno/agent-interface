"""Independent bitmask oracle plus preconditioned mutation audit."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
VARIABLES = ("x", "y", "z")
DOMAIN = tuple(itertools.product((0, 1), repeat=3))
EQ = [
    {"name": "xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
]
APPROX = [{**context, "spread": 0.5} for context in EQ]
ODD = [*EQ[:2], {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]], "spread": 1.0}]
SHORT = EQ[:2]
FIXED = {
    "exact": (EQ, True, 0.0),
    "within_tolerance": (APPROX, True, 0.5),
    "beyond_tolerance": (APPROX, True, 0.5),
    "no_global_section": (ODD, True, 1.0),
    "missing_context": (SHORT, False, 1.0),
}
TOLERANCES = (0.0, 0.5, 1.0)
CONTRACTS = ("exact_only", "reversible_approximate",
             "explicit_allow_approximate_irreversible")
ACTIONS = ("reversible", "compensable", "irreversible")


def oracle(decision_input):
    valid = (1 << len(DOMAIN)) - 1
    for context in decision_input["contexts"]:
        relation_mask = 0
        allowed = {tuple(values) for values in context["tuples"]}
        for index, assignment in enumerate(DOMAIN):
            projection = tuple(assignment[VARIABLES.index(name)] for name in context["vars"])
            if projection in allowed:
                relation_mask |= 1 << index
        valid &= relation_mask
    sections = [{name: DOMAIN[i][j] for j, name in enumerate(VARIABLES)}
                for i in range(len(DOMAIN)) if valid & (1 << i)]
    spread = max((context["spread"] for context in decision_input["contexts"]), default=0.0)
    if not decision_input["complete"]:
        status = "UNKNOWN"
    elif not sections:
        status = "NO_GLOBAL_SECTION"
    elif spread == 0.0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif spread <= decision_input["tolerance"]:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        admitted = decision_input["action"] in ACTIONS[:2] or (
            decision_input["action"] == "irreversible" and
            decision_input["contract"] == "explicit_allow_approximate_irreversible")
    return {"sections": sections, "section_count": len(sections), "spread": spread,
            "status": status, "admitted": admitted}


def check(rows):
    errors, seen, keys = [], set(), set()
    expected = {(case, tol, contract, action) for case in FIXED for tol in TOLERANCES
                for contract in CONTRACTS for action in ACTIONS}
    if len(rows) != 135:
        errors.append("row_count")
    for i, row in enumerate(rows):
        if set(row) != {"decision_input", "decision_output", "record_id"}:
            errors.append(f"row_shape:{i}")
        source, output = row.get("decision_input", {}), row.get("decision_output", {})
        key = (source.get("case"), source.get("tolerance"), source.get("contract"), source.get("action"))
        if key[0] not in FIXED or key[1] not in TOLERANCES or key[2] not in CONTRACTS or key[3] not in ACTIONS:
            errors.append(f"input_domain:{i}")
            continue
        keys.add(key)
        if key in seen:
            errors.append(f"duplicate:{i}")
        seen.add(key)
        contexts, complete, declared = FIXED[key[0]]
        expected_input = {"case": key[0], "contexts": contexts, "complete": complete,
                          "declared_spread": declared, "tolerance": key[1],
                          "contract": key[2], "action": key[3]}
        if source != expected_input:
            errors.append(f"decision_input:{i}")
        expected_output = oracle(expected_input)
        if output != expected_output:
            errors.append(f"decision_output:{i}")
        payload = {name: value for name, value in row.items() if name != "record_id"}
        rid = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()
        if row.get("record_id") != rid or rid in seen:
            errors.append(f"record_id:{i}")
        seen.add(rid)
    if keys != expected:
        errors.append("matrix_coverage")
    return errors


def mutation_manifest(rows):
    def locate(case, tol, contract, action):
        selected = [r for r in rows if (r["decision_input"]["case"], r["decision_input"]["tolerance"],
                                        r["decision_input"]["contract"], r["decision_input"]["action"]) ==
                   (case, tol, contract, action)]
        if len(selected) != 1:
            raise AssertionError(f"selector not unique: {case,tol,contract,action}: {len(selected)}")
        return selected[0]
    return [
        ("false_approx_irreversible_admission", locate("within_tolerance", 0.5,
         "reversible_approximate", "irreversible"), ("decision_output", "admitted"), False, True),
        ("false_status", locate("within_tolerance", 0.5, "reversible_approximate", "irreversible"),
         ("decision_output", "status"), "APPROXIMATE_SECTION", "NO_GLOBAL_SECTION"),
        ("changed_tolerance", locate("exact", 0.0, "exact_only", "reversible"),
         ("decision_input", "tolerance"), 0.0, 0.25),
        ("changed_fixture_spread", locate("within_tolerance", 0.5, "exact_only", "reversible"),
         ("decision_input", "declared_spread"), 0.5, 0.75),
        ("dropped_row", rows[-1], ("__row_count__", "__row_count__"), 135, 134),
        ("duplicated_row", rows[0], ("__duplicate__", "__duplicate__"), False, True),
    ]


def mutate(rows, name, entry):
    changed = copy.deepcopy(rows)
    _, row, (section, field), before, after = entry
    if section == "__row_count__":
        if len(changed) != before:
            raise AssertionError("row-count mutation precondition")
        changed.pop()
        if len(changed) != after:
            raise AssertionError("row-count mutation postcondition")
    elif section == "__duplicate__":
        if len(changed) != 135:
            raise AssertionError("duplicate mutation precondition")
        changed.append(copy.deepcopy(changed[0]))
        if len(changed) != 136:
            raise AssertionError("duplicate mutation postcondition")
    else:
        idx = next(i for i, candidate in enumerate(changed)
                   if candidate["decision_input"] == row["decision_input"])
        selected = changed[idx][section]
        if selected.get(field) != before:
            raise AssertionError(f"{name} before-value mismatch: {selected.get(field)!r} != {before!r}")
        selected[field] = after
        if selected[field] == before:
            raise AssertionError(f"{name} mutation is identity")
        payload = {k: v for k, v in changed[idx].items() if k != "record_id"}
        changed[idx]["record_id"] = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if changed == rows:
        raise AssertionError(f"{name} document mutation is identity")
    return changed


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base_errors = check(rows)
    controls = {}
    for name, *rest in mutation_manifest(rows):
        entry = (name, *rest)
        changed = mutate(rows, name, entry)
        controls[name] = {"nonidentity": changed != rows, "rejected": bool(check(changed))}
    passed = not base_errors and all(v["nonidentity"] and v["rejected"] for v in controls.values())
    receipt = {"status": "PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED" if passed else "STOP_AUDIT_MISMATCH",
               "rows": len(rows), "base_errors": base_errors, "mutation_controls": controls,
               "mutation_count": len(controls),
               "mutations_nonidentity": sum(v["nonidentity"] for v in controls.values()),
               "mutations_rejected": sum(v["rejected"] for v in controls.values()),
               "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    (RAW.parent / "audit.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
