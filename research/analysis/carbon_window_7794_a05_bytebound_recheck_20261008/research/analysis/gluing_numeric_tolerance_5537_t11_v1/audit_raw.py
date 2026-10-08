"""Independent Fraction-based minimax oracle and mutation auditor."""
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
VARS = ("x", "y", "z")
GRID = tuple(Fraction(value, 8) for value in (0, 2, 4, 6, 8))
EXACT = [{"left": "x", "right": "y", "target_ticks": 0},
         {"left": "y", "right": "z", "target_ticks": 0},
         {"left": "z", "right": "x", "target_ticks": 0}]
NEAR = [*EXACT[:2], {"left": "z", "right": "x", "target_ticks": 4}]
FAR = [*EXACT[:2], {"left": "z", "right": "x", "target_ticks": 8}]
FIXTURES = {"exact_cycle": (EXACT, True), "near_cycle": (NEAR, True),
            "far_cycle": (FAR, True), "missing_context": (NEAR[:2], False)}
TOLERANCES = (0, 1, 2, 4)
CONTRACTS = ("exact_only", "reversible_approximate",
             "explicit_allow_approximate_irreversible")
ACTIONS = ("reversible", "compensable", "irreversible")


def reference(source):
    scored = []
    for values in itertools.product(GRID, repeat=3):
        assignment = dict(zip(VARS, values))
        residuals = [abs((assignment[edge["right"]] - assignment[edge["left"]])
                         - Fraction(edge["target_ticks"], 8))
                     for edge in source["relations"]]
        score = max(residuals, default=Fraction(0))
        scored.append((score, assignment, residuals))
    best = min((item[0] for item in scored), default=None)
    best_rows = [(assignment, residuals) for score, assignment, residuals in scored if score == best]
    best_ticks = None if best is None else int(best * 8)
    tolerance = Fraction(source["tolerance_ticks"], 8)
    if not source["complete"]:
        status = "UNKNOWN"
    elif best == 0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif best is not None and best <= tolerance:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        contract, action = source["contract"], source["action"]
        admitted = contract == "reversible_approximate" and action in ACTIONS[:2]
        admitted |= contract == "explicit_allow_approximate_irreversible" and action in ACTIONS
    witnesses = [{"assignment_ticks": {name: int(value * 8) for name, value in assignment.items()},
                  "residual_ticks": [int(value * 8) for value in residuals]}
                 for assignment, residuals in best_rows]
    return {"minimax_residual_ticks": best_ticks, "optimal_witnesses": witnesses,
            "optimal_witness_count": len(witnesses), "status": status, "admitted": admitted}


def expected_input(case, tolerance, contract, action):
    relations, complete = FIXTURES[case]
    return {"case": case, "relations": relations, "complete": complete,
            "tolerance_ticks": tolerance, "contract": contract, "action": action}


def check(rows):
    errors, observed, record_ids = [], set(), set()
    expected = {(case, tolerance, contract, action) for case in FIXTURES
                for tolerance in TOLERANCES for contract in CONTRACTS for action in ACTIONS}
    if len(rows) != 144:
        errors.append("row_count")
    for index, row in enumerate(rows):
        if set(row) != {"decision_input", "decision_output", "record_id"}:
            errors.append(f"row_shape:{index}")
        source = row.get("decision_input", {})
        key = (source.get("case"), source.get("tolerance_ticks"), source.get("contract"), source.get("action"))
        if key[0] not in FIXTURES or key[1] not in TOLERANCES or key[2] not in CONTRACTS or key[3] not in ACTIONS:
            errors.append(f"input_domain:{index}")
            continue
        if key in observed:
            errors.append(f"duplicate_key:{index}")
        observed.add(key)
        fixed = expected_input(*key)
        if source != fixed:
            errors.append(f"decision_input:{index}")
        if row.get("decision_output") != reference(fixed):
            errors.append(f"decision_output:{index}")
        payload = {k: v for k, v in row.items() if k != "record_id"}
        rid = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()
        if row.get("record_id") != rid or rid in record_ids:
            errors.append(f"record_id:{index}")
        record_ids.add(rid)
    if observed != expected:
        errors.append("matrix_coverage")
    return errors


def mutation_manifest(rows):
    def find(case, tol, contract, action):
        found = [r for r in rows if (r["decision_input"]["case"], r["decision_input"]["tolerance_ticks"],
                                     r["decision_input"]["contract"], r["decision_input"]["action"]) ==
                (case, tol, contract, action)]
        if len(found) != 1:
            raise AssertionError(f"selector count {len(found)} for {case,tol,contract,action}")
        return found[0]
    return [
        ("false_irreversible_admission", find("near_cycle", 2, "reversible_approximate", "irreversible"),
         "decision_output", "admitted", False, True),
        ("false_status", find("near_cycle", 2, "exact_only", "reversible"),
         "decision_output", "status", "APPROXIMATE_SECTION", "NO_GLOBAL_SECTION"),
        ("unsafe_over_tolerance_admission", find("near_cycle", 1,
         "explicit_allow_approximate_irreversible", "irreversible"),
         "decision_output", "admitted", False, True),
        ("changed_tolerance", find("exact_cycle", 0, "exact_only", "reversible"),
         "decision_input", "tolerance_ticks", 0, 1),
        ("changed_relation", find("near_cycle", 2, "exact_only", "reversible"),
         "decision_input", "relations", NEAR, FAR),
        ("dropped_row", None, None, None, 144, 143),
    ]


def mutate(rows, name, entry):
    changed = json.loads(json.dumps(rows))
    _, target, section, field, before, after = entry
    if name == "dropped_row":
        if len(changed) != before:
            raise AssertionError("drop precondition")
        changed.pop()
        if len(changed) != after:
            raise AssertionError("drop postcondition")
    else:
        key = target["decision_input"]
        positions = [i for i, row in enumerate(changed) if row["decision_input"] == key]
        if len(positions) != 1:
            raise AssertionError("mutation selector not unique")
        row = changed[positions[0]][section]
        if row.get(field) != before:
            raise AssertionError(f"{name} before mismatch: {row.get(field)!r} != {before!r}")
        row[field] = after
        if row[field] == before:
            raise AssertionError(f"{name} is identity")
        payload = {k: v for k, v in changed[positions[0]].items() if k != "record_id"}
        changed[positions[0]]["record_id"] = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if changed == rows:
        raise AssertionError(f"{name} document unchanged")
    return changed


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base_errors = check(rows)
    controls = {}
    for name, *rest in mutation_manifest(rows):
        altered = mutate(rows, name, (name, *rest))
        controls[name] = {"nonidentity": altered != rows, "rejected": bool(check(altered))}
    okay = not base_errors and all(v["nonidentity"] and v["rejected"] for v in controls.values())
    receipt = {"status": "PASS_NUMERIC_APPROXIMATE_SECTION_SCOPED" if okay else "STOP_AUDIT_MISMATCH",
               "rows": len(rows), "base_errors": base_errors, "mutation_controls": controls,
               "mutation_count": len(controls), "mutations_nonidentity": sum(v["nonidentity"] for v in controls.values()),
               "mutations_rejected": sum(v["rejected"] for v in controls.values()),
               "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    (RAW.parent / "audit.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    if not okay:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
