"""Separately implemented exhaustive raw-only decision and mutation audit."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
VARS = ("x", "y", "z")
EQ = [
    {"name": "xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
]
PARITY = [*EQ[:2], {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]], "spread": 1.0}]
WIDE = [{**c, "spread": 0.5} for c in EQ]
MISSING = EQ[:2]
FIXTURES = {"exact": (EQ, True, 0.0), "within_tolerance": (WIDE, True, 0.5),
            "beyond_tolerance": (WIDE, True, 0.5), "parity_empty": (PARITY, True, 1.0),
            "missing_context": (MISSING, False, 0.0)}
EXPECTED_ROWS = 5 * 3 * 3 * 3


def oracle(contexts, complete, tolerance, action, override):
    compatible = []
    for bits in itertools.product((0, 1), repeat=len(VARS)):
        assignment = dict(zip(VARS, bits))
        if all(any(tuple(assignment[name] for name in context["vars"]) == tuple(candidate)
                   for candidate in context["tuples"]) for context in contexts):
            compatible.append(assignment)
    spread = max((float(c["spread"]) for c in contexts), default=0.0)
    if not complete:
        status = "UNKNOWN"
    elif not compatible:
        status = "NO_GLOBAL_SECTION"
    elif spread == 0.0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif spread <= tolerance:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        admitted = action in ("reversible", "compensable") or (action == "irreversible" and override)
    return compatible, spread, status, admitted


def audit(rows):
    errors, seen = [], set()
    if len(rows) != EXPECTED_ROWS:
        errors.append("row_count")
    expected_keys = set()
    for row in rows:
        case = row.get("case")
        if case not in FIXTURES:
            errors.append("unknown_case")
            continue
        contexts, complete, declared_spread = FIXTURES[case]
        if row.get("contexts") != contexts or row.get("complete") is not complete:
            errors.append("fixture_mismatch")
        if row.get("declared_spread") != declared_spread:
            errors.append("declared_spread_mismatch")
        tolerance, policy, action = row.get("tolerance"), row.get("policy"), row.get("action_class")
        override = row.get("allow_approx_irreversible")
        if tolerance not in (0.0, 0.5, 1.0) or policy not in (
                "exact_only", "approx_reversible_only", "explicit_approx_irreversible_contract"):
            errors.append("policy_domain")
            continue
        if action not in ("reversible", "compensable", "irreversible"):
            errors.append("action_domain")
            continue
        if override is not (policy == "explicit_approx_irreversible_contract"):
            errors.append("override_policy_binding")
        expected_keys.add((case, tolerance, policy, action))
        sections, spread, status, admitted = oracle(contexts, complete, tolerance, action, override)
        expected = {"sections": sections, "section_count": len(sections), "spread": spread,
                    "status": status, "admitted": admitted}
        for field, value in expected.items():
            if row.get(field) != value:
                errors.append(f"decision:{field}:{case}:{tolerance}:{policy}:{action}")
        if case == "within_tolerance" and tolerance == 0.5 and action == "irreversible":
            should_admit = policy == "explicit_approx_irreversible_contract"
            if admitted != should_admit:
                errors.append("irreversible_approx_boundary")
        payload = {k: v for k, v in row.items() if k != "record_id"}
        record_id = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()
        if row.get("record_id") != record_id or record_id in seen:
            errors.append("record_identity")
        seen.add(record_id)
    if len(expected_keys) != EXPECTED_ROWS:
        errors.append("case_matrix_coverage")
    return errors


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base_errors = audit(rows)
    controls = {}
    for name, mutate in (
        ("false_irreversible_admission", lambda rs: rs[1].__setitem__("admitted", True)),
        ("false_global_status", lambda rs: rs[0].__setitem__("status", "APPROXIMATE_SECTION")),
        ("changed_tolerance", lambda rs: rs[0].__setitem__("tolerance", 0.25)),
        ("dropped_row", lambda rs: rs.pop()),
        ("duplicated_row", lambda rs: rs.append(dict(rs[0]))),
    ):
        corrupted = [dict(row) for row in rows]
        mutate(corrupted)
        controls[name] = bool(audit(corrupted))
    okay = not base_errors and all(controls.values())
    result = {"status": "PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED" if okay else "STOP_AUDIT_MISMATCH",
              "rows": len(rows), "errors": base_errors, "mutation_controls": controls,
              "mutation_rejections": sum(controls.values()), "mutation_count": len(controls),
              "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    out = RAW.with_name("audit.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not okay:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
