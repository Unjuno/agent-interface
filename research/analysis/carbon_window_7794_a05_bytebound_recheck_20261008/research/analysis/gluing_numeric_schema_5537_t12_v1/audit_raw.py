"""Independent strict-schema Fraction oracle and T12 corruption auditor."""
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
EDGE_KEYS = {"left", "right", "target_ticks"}
OUTPUT_KEYS = {"observed_subgraph_minimax_residual_ticks", "residual_scope",
               "minimax_residual_ticks", "optimal_witnesses", "optimal_witness_count",
               "status", "admitted"}
STATUSES = {"UNKNOWN", "GLOBAL_SECTION_CERTIFIED", "APPROXIMATE_SECTION", "NO_GLOBAL_SECTION"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def valid_input(source):
    if type(source) is not dict or set(source) != {
            "case", "relations", "complete", "tolerance_ticks", "contract", "action"}:
        return False
    if type(source["case"]) is not str or source["case"] not in FIXTURES:
        return False
    if type(source["complete"]) is not bool:
        return False
    if type(source["tolerance_ticks"]) is not int or source["tolerance_ticks"] not in TOLERANCES:
        return False
    if type(source["contract"]) is not str or source["contract"] not in CONTRACTS:
        return False
    if type(source["action"]) is not str or source["action"] not in ACTIONS:
        return False
    if type(source["relations"]) is not list or not source["relations"]:
        return False
    for edge in source["relations"]:
        if type(edge) is not dict or set(edge) != EDGE_KEYS:
            return False
        if type(edge["left"]) is not str or edge["left"] not in VARS:
            return False
        if type(edge["right"]) is not str or edge["right"] not in VARS:
            return False
        if type(edge["target_ticks"]) is not int or edge["target_ticks"] not in (0, 4, 8):
            return False
    relations, complete = FIXTURES[source["case"]]
    return source["relations"] == relations and source["complete"] is complete


def valid_output(output, relation_count):
    if type(output) is not dict or set(output) != OUTPUT_KEYS:
        return False
    observed = output["observed_subgraph_minimax_residual_ticks"]
    if type(observed) is not int or observed < 0:
        return False
    if type(output["residual_scope"]) is not str or output["residual_scope"] not in (
            "full_cover", "observed_subgraph_only"):
        return False
    minimax = output["minimax_residual_ticks"]
    if minimax is not None and (type(minimax) is not int or minimax < 0):
        return False
    if type(output["optimal_witnesses"]) is not list:
        return False
    if type(output["optimal_witness_count"]) is not int or output["optimal_witness_count"] < 0:
        return False
    if type(output["status"]) is not str or output["status"] not in STATUSES:
        return False
    if type(output["admitted"]) is not bool:
        return False
    for witness in output["optimal_witnesses"]:
        if type(witness) is not dict or set(witness) != {"assignment_ticks", "residual_ticks"}:
            return False
        assignment, residuals = witness["assignment_ticks"], witness["residual_ticks"]
        if type(assignment) is not dict or set(assignment) != set(VARS):
            return False
        if any(type(value) is not int or value not in (0, 2, 4, 6, 8)
               for value in assignment.values()):
            return False
        if type(residuals) is not list or len(residuals) != relation_count:
            return False
        if any(type(value) is not int or value < 0 for value in residuals):
            return False
    if output["residual_scope"] == "observed_subgraph_only":
        return minimax is None and not output["optimal_witnesses"] and output["optimal_witness_count"] == 0
    return minimax == observed and output["optimal_witness_count"] == len(output["optimal_witnesses"])


def reference(source):
    scored = []
    for values in itertools.product(GRID, repeat=3):
        assignment = dict(zip(VARS, values))
        residuals = [abs((assignment[edge["right"]] - assignment[edge["left"]])
                         - Fraction(edge["target_ticks"], 8)) for edge in source["relations"]]
        score = max(residuals, default=Fraction(0))
        scored.append((score, assignment, residuals))
    observed = min(row[0] for row in scored)
    witnesses = [(assignment, residuals) for score, assignment, residuals in scored if score == observed]
    observed_ticks = int(observed * 8)
    complete = source["complete"]
    if not complete:
        status = "UNKNOWN"
    elif observed == 0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif observed <= Fraction(source["tolerance_ticks"], 8):
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        contract, action = source["contract"], source["action"]
        admitted = contract == "reversible_approximate" and action in ACTIONS[:2]
        admitted |= contract == "explicit_allow_approximate_irreversible" and action in ACTIONS
    return {
        "observed_subgraph_minimax_residual_ticks": observed_ticks,
        "residual_scope": "full_cover" if complete else "observed_subgraph_only",
        "minimax_residual_ticks": observed_ticks if complete else None,
        "optimal_witnesses": ([{"assignment_ticks": {name: int(value * 8) for name, value in assignment.items()},
                                "residual_ticks": [int(value * 8) for value in residuals]}
                               for assignment, residuals in witnesses] if complete else []),
        "optimal_witness_count": len(witnesses) if complete else 0,
        "status": status,
        "admitted": admitted,
    }


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
        if type(row) is not dict or set(row) != {"decision_input", "decision_output", "record_id"}:
            errors.append(f"row_shape:{index}")
            continue
        source, output = row["decision_input"], row["decision_output"]
        if not valid_input(source):
            errors.append(f"input_schema:{index}")
            continue
        key = (source["case"], source["tolerance_ticks"], source["contract"], source["action"])
        if key not in expected:
            errors.append(f"input_domain:{index}")
            continue
        if key in observed:
            errors.append(f"duplicate_key:{index}")
        observed.add(key)
        fixed = expected_input(*key)
        if source != fixed:
            errors.append(f"decision_input:{index}")
        if not valid_output(output, len(source["relations"])):
            errors.append(f"output_schema:{index}")
        if output != reference(fixed):
            errors.append(f"decision_output:{index}")
        payload = {key: value for key, value in row.items() if key != "record_id"}
        rid = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()
        if type(row["record_id"]) is not str or row["record_id"] != rid or rid in record_ids:
            errors.append(f"record_id:{index}")
        record_ids.add(rid)
    if observed != expected:
        errors.append("matrix_coverage")
    return errors


def mutation_manifest(rows):
    def find(case, tolerance, contract, action):
        matches = [row for row in rows if (row["decision_input"]["case"],
                    row["decision_input"]["tolerance_ticks"], row["decision_input"]["contract"],
                    row["decision_input"]["action"]) == (case, tolerance, contract, action)]
        if len(matches) != 1:
            raise AssertionError(f"selector count {len(matches)}")
        return matches[0]
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
        ("incomplete_full_residual_promotion", find("missing_context", 0, "exact_only", "reversible"),
         "decision_output", "minimax_residual_ticks", None, 0),
        ("incomplete_witness_promotion", find("missing_context", 0, "exact_only", "reversible"),
         "decision_output", "optimal_witnesses", [],
         [{"assignment_ticks": {"x": 0, "y": 0, "z": 0}, "residual_ticks": [0, 0]}]),
        ("boolean_tolerance_alias", find("exact_cycle", 0, "exact_only", "reversible"),
         "decision_input", "tolerance_ticks", 0, False),
        ("unknown_endpoint", find("near_cycle", 2, "exact_only", "reversible"),
         "decision_input", "relations", NEAR, [{**NEAR[0], "left": "q"}, *NEAR[1:]]),
        ("out_of_range_target", find("near_cycle", 2, "exact_only", "reversible"),
         "decision_input", "relations", NEAR, [*NEAR[:2], {**NEAR[2], "target_ticks": 99}]),
        ("unknown_contract", find("exact_cycle", 0, "exact_only", "reversible"),
         "decision_input", "contract", "exact_only", "unregistered"),
        ("unknown_action", find("exact_cycle", 0, "exact_only", "reversible"),
         "decision_input", "action", "reversible", "unknown"),
        ("malformed_completeness", find("missing_context", 0, "exact_only", "reversible"),
         "decision_input", "complete", False, "false"),
        ("boolean_output_alias", find("missing_context", 0, "exact_only", "reversible"),
         "decision_output", "admitted", False, 0),
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
        positions = [i for i, row in enumerate(changed) if row["decision_input"] == target["decision_input"]]
        if len(positions) != 1:
            raise AssertionError(f"{name}: selector not unique")
        index = positions[0]
        record = changed[index][section]
        if canonical(record.get(field)) != canonical(before):
            raise AssertionError(f"{name}: before mismatch")
        record[field] = after
        if canonical(record[field]) == canonical(before):
            raise AssertionError(f"{name}: identity mutation")
        payload = {key: value for key, value in changed[index].items() if key != "record_id"}
        changed[index]["record_id"] = hashlib.sha256(canonical(payload)).hexdigest()
    if canonical(changed) == canonical(rows):
        raise AssertionError(f"{name}: unchanged corpus")
    return changed


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base_errors = check(rows)
    controls = {}
    for name, *rest in mutation_manifest(rows):
        altered = mutate(rows, name, (name, *rest))
        controls[name] = {"nonidentity": canonical(altered) != canonical(rows),
                          "rejected": bool(check(altered))}
    okay = not base_errors and len(controls) == 15 and all(
        result["nonidentity"] and result["rejected"] for result in controls.values())
    receipt = {"status": "PASS_SCOPE_SAFE_STRICT_SCHEMA_SCOPED" if okay else "STOP_AUDIT_MISMATCH",
               "rows": len(rows), "base_errors": base_errors, "mutation_controls": controls,
               "mutation_count": len(controls),
               "mutations_nonidentity": sum(result["nonidentity"] for result in controls.values()),
               "mutations_rejected": sum(result["rejected"] for result in controls.values()),
               "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    (RAW.parent / "audit.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    if not okay:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
