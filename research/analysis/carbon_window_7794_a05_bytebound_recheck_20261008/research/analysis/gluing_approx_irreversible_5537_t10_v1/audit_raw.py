"""Independent bitmask relation oracle and mutation auditor for T10."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
NAMES = ("x", "y", "z")
DOMAIN = tuple(itertools.product((0, 1), repeat=3))
BASE = [
    {"name": "xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
]
NEAR = [{**context, "spread": 0.5} for context in BASE]
ODD = [*BASE[:2], {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]], "spread": 1.0}]
SHORT = BASE[:2]
FIXTURES = {
    "exact": (BASE, True, 0.0),
    "within_tolerance": (NEAR, True, 0.5),
    "beyond_tolerance": (NEAR, True, 0.5),
    "no_global_section": (ODD, True, 1.0),
    "missing_context": (SHORT, False, 1.0),
}
TOLERANCES = (0.0, 0.25, 0.5, 1.0)
CONTRACTS = ("exact_only", "reversible_approximate",
             "explicit_allow_approximate_irreversible")
ACTIONS = ("reversible", "compensable", "irreversible")


def oracle(source):
    mask = (1 << len(DOMAIN)) - 1
    for context in source["contexts"]:
        local_mask = 0
        relation = {tuple(pair) for pair in context["tuples"]}
        for index, assignment in enumerate(DOMAIN):
            projection = tuple(assignment[NAMES.index(v)] for v in context["vars"])
            if projection in relation:
                local_mask |= 1 << index
        mask &= local_mask
    sections = [{name: DOMAIN[i][j] for j, name in enumerate(NAMES)}
                for i in range(len(DOMAIN)) if mask & (1 << i)]
    spread = max((context["spread"] for context in source["contexts"]), default=0.0)
    if not source["complete"]:
        status = "UNKNOWN"
    elif not sections:
        status = "NO_GLOBAL_SECTION"
    elif spread == 0.0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif spread <= source["tolerance"]:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        admitted = source["contract"] == "reversible_approximate" and source["action"] in ACTIONS[:2]
        admitted |= (source["contract"] == "explicit_allow_approximate_irreversible"
                     and source["action"] in ACTIONS)
    return {"sections": sections, "section_count": len(sections), "spread": spread,
            "status": status, "admitted": admitted}


def expected_input(case, tolerance, contract, action):
    contexts, complete, declared = FIXTURES[case]
    return {"case": case, "contexts": contexts, "complete": complete,
            "declared_spread": declared, "tolerance": tolerance,
            "contract": contract, "action": action}


def check(rows):
    errors, observed, seen_ids = [], set(), set()
    expected_keys = {(case, tolerance, contract, action) for case in FIXTURES
                     for tolerance in TOLERANCES for contract in CONTRACTS for action in ACTIONS}
    if len(rows) != 180:
        errors.append("row_count")
    for index, row in enumerate(rows):
        if set(row) != {"decision_input", "decision_output", "record_id"}:
            errors.append(f"row_shape:{index}")
        source = row.get("decision_input", {})
        key = (source.get("case"), source.get("tolerance"), source.get("contract"), source.get("action"))
        if key[0] not in FIXTURES or key[1] not in TOLERANCES or key[2] not in CONTRACTS or key[3] not in ACTIONS:
            errors.append(f"input_domain:{index}")
            continue
        if key in observed:
            errors.append(f"duplicate_key:{index}")
        observed.add(key)
        fixture_input = expected_input(*key)
        if source != fixture_input:
            errors.append(f"input_fixture:{index}")
        if row.get("decision_output") != oracle(fixture_input):
            errors.append(f"output_oracle:{index}")
        payload = {k: v for k, v in row.items() if k != "record_id"}
        record_id = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()
        if row.get("record_id") != record_id or record_id in seen_ids:
            errors.append(f"record_id:{index}")
        seen_ids.add(record_id)
    if observed != expected_keys:
        errors.append("matrix_coverage")
    return errors


def mutation_manifest(rows):
    def find(case, tolerance, contract, action):
        selected = [r for r in rows if (r["decision_input"]["case"], r["decision_input"]["tolerance"],
                                        r["decision_input"]["contract"], r["decision_input"]["action"]) ==
                   (case, tolerance, contract, action)]
        if len(selected) != 1:
            raise AssertionError(f"non-unique mutation selector: {case,tolerance,contract,action}")
        return selected[0]
    return [
        ("false_irreversible_admission", find("within_tolerance", 0.5,
          "reversible_approximate", "irreversible"), "decision_output", "admitted", False, True),
        ("false_status", find("within_tolerance", 0.5, "exact_only", "reversible"),
         "decision_output", "status", "APPROXIMATE_SECTION", "NO_GLOBAL_SECTION"),
        ("unsafe_beyond_tolerance_admission", find("beyond_tolerance", 0.25,
          "explicit_allow_approximate_irreversible", "irreversible"),
         "decision_output", "admitted", False, True),
        ("changed_tolerance", find("exact", 0.0, "exact_only", "reversible"),
         "decision_input", "tolerance", 0.0, 0.25),
        ("dropped_row", None, None, None, 180, 179),
        ("duplicated_row", None, None, None, 180, 181),
    ]


def mutate(rows, name, entry):
    changed = copy.deepcopy(rows)
    _, target, section, field, before, after = entry
    if name == "dropped_row":
        if len(changed) != before:
            raise AssertionError("drop precondition")
        changed.pop()
        if len(changed) != after:
            raise AssertionError("drop postcondition")
    elif name == "duplicated_row":
        if len(changed) != before:
            raise AssertionError("duplicate precondition")
        changed.append(copy.deepcopy(changed[0]))
        if len(changed) != after:
            raise AssertionError("duplicate postcondition")
    else:
        key = target["decision_input"]
        indexes = [i for i, row in enumerate(changed) if row["decision_input"] == key]
        if len(indexes) != 1:
            raise AssertionError(f"mutation target ambiguity: {name}")
        value = changed[indexes[0]][section].get(field)
        if value != before:
            raise AssertionError(f"{name} precondition: {value!r} != {before!r}")
        changed[indexes[0]][section][field] = after
        if changed[indexes[0]][section][field] == before:
            raise AssertionError(f"{name} identity mutation")
        payload = {k: v for k, v in changed[indexes[0]].items() if k != "record_id"}
        changed[indexes[0]]["record_id"] = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if changed == rows:
        raise AssertionError(f"{name} entire document unchanged")
    return changed


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base_errors = check(rows)
    controls = {}
    for name, *rest in mutation_manifest(rows):
        entry = (name, *rest)
        altered = mutate(rows, name, entry)
        controls[name] = {"nonidentity": altered != rows, "rejected": bool(check(altered))}
    okay = not base_errors and all(result["nonidentity"] and result["rejected"]
                                   for result in controls.values())
    receipt = {"status": "PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED" if okay else "STOP_AUDIT_MISMATCH",
               "rows": len(rows), "base_errors": base_errors, "mutation_controls": controls,
               "mutation_count": len(controls),
               "mutations_nonidentity": sum(x["nonidentity"] for x in controls.values()),
               "mutations_rejected": sum(x["rejected"] for x in controls.values()),
               "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    (RAW.parent / "audit.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    if not okay:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
