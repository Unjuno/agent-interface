"""Corrected raw-only auditor for the immutable T0 candidate trace."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

FIELDS = ("evidence_present", "evidence_fresh", "authority_matches", "outcome_known")
KEYS = (*FIELDS, "terminal_failure")
MUTANTS = (
    "drop_provenance",
    "accept_stale",
    "ignore_authority",
    "commit_unknown",
    "reactivate_terminal",
    "compound_provenance_authority_terminal",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specification(state):
    return (state["evidence_present"] and state["evidence_fresh"]
            and state["authority_matches"] and state["outcome_known"]
            and not state["terminal_failure"])


def independent_mutation_semantics(state, operator):
    if (operator == "compound_provenance_authority_terminal"
            and not state["evidence_present"]
            and not state["authority_matches"]
            and state["terminal_failure"]):
        return True
    required_fields = {
        "drop_provenance": ("evidence_fresh", "authority_matches", "outcome_known"),
        "accept_stale": ("evidence_present", "authority_matches", "outcome_known"),
        "ignore_authority": ("evidence_present", "evidence_fresh", "outcome_known"),
        "commit_unknown": ("evidence_present", "evidence_fresh", "authority_matches"),
        "reactivate_terminal": ("evidence_present", "evidence_fresh",
                                "authority_matches", "outcome_known"),
        "compound_provenance_authority_terminal": FIELDS,
    }[operator]
    return (all(state[field] for field in required_fields)
            and (operator == "reactivate_terminal" or not state["terminal_failure"]))


def audit(raw_path, output_path):
    raw_path = Path(raw_path)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "issue5541-mutation-adequacy-t0-v1":
        errors.append("schema_mismatch")
    if tuple(raw.get("field_order", ())) != KEYS:
        errors.append("field_order_mismatch")
    if tuple(raw.get("mutants", ())) != MUTANTS:
        errors.append("mutant_inventory_mismatch")

    expected_states = {
        tuple(values) for values in itertools.product((False, True), repeat=len(KEYS))
    }
    actual_states = {
        tuple(row.get("state", {}).get(field) for field in KEYS)
        for row in raw.get("exhaustive", [])
    }
    if actual_states != expected_states or len(raw.get("exhaustive", [])) != 32:
        errors.append("exhaustive_state_inventory_incomplete_or_duplicate")

    kill = {
        name: {"baseline": False, "metamorphic": False, "independent_exhaustive": False}
        for name in MUTANTS
    }
    expected_baseline = {
        "nominal_commit": True,
        "missing_provenance": False,
        "unknown_outcome": False,
    }
    baseline = {row.get("case"): row for row in raw.get("baseline", [])}
    if set(baseline) != set(expected_baseline):
        errors.append("baseline_inventory_mismatch")
    for case, expected in expected_baseline.items():
        row = baseline.get(case)
        if row is None:
            continue
        state = row.get("state", {})
        if (row.get("expected_commit") is not expected
                or specification(state) is not expected
                or row.get("decisions", {}).get("candidate") is not expected):
            errors.append(f"baseline_contract_mismatch:{case}")
        for mutant in MUTANTS:
            if row.get("decisions", {}).get(mutant) is not expected:
                kill[mutant]["baseline"] = True

    relations = {
        "degrade_evidence_fresh_must_not_commit": ("evidence_fresh", True, False),
        "degrade_authority_matches_must_not_commit": ("authority_matches", True, False),
        "degrade_terminal_failure_must_not_commit": ("terminal_failure", False, True),
    }
    metamorphic = {row.get("relation"): row for row in raw.get("metamorphic", [])}
    if set(metamorphic) != set(relations):
        errors.append("metamorphic_inventory_mismatch")
    for relation, (field, base_value, degraded_value) in relations.items():
        row = metamorphic.get(relation)
        if row is None:
            continue
        base, degraded = row.get("base_state", {}), row.get("degraded_state", {})
        if (base.get(field) is not base_value or degraded.get(field) is not degraded_value
                or not specification(base) or specification(degraded)):
            errors.append(f"metamorphic_contract_mismatch:{relation}")
        if (row.get("base_decisions", {}).get("candidate") is not True
                or row.get("degraded_decisions", {}).get("candidate") is not False):
            errors.append(f"candidate_metamorphic_mismatch:{relation}")
        for mutant in MUTANTS:
            if row.get("degraded_decisions", {}).get(mutant) is not False:
                kill[mutant]["metamorphic"] = True

    for row in raw.get("exhaustive", []):
        state, observed = row.get("state", {}), row.get("decisions", {})
        expected = specification(state)
        if observed.get("candidate") is not expected:
            errors.append(f"candidate_spec_mismatch:{tuple(state.get(k) for k in KEYS)}")
        for mutant in MUTANTS:
            mutant_expected = independent_mutation_semantics(state, mutant)
            if observed.get(mutant) is not mutant_expected:
                errors.append(f"mutant_trace_mismatch:{mutant}:{tuple(state.get(k) for k in KEYS)}")
            if mutant_expected is not expected:
                kill[mutant]["independent_exhaustive"] = True

    matrix = {}
    for mutant, oracles in kill.items():
        non_equivalent = oracles["independent_exhaustive"]
        killed = any(oracles.values())
        matrix[mutant] = {**oracles, "non_equivalent": non_equivalent,
                          "killed_by_declared_oracles": killed}
        if non_equivalent and not killed:
            errors.append(f"surviving_safety_mutant:{mutant}")

    output = {
        "schema": "issue5541-mutation-adequacy-audit-v2",
        "disposition": "corrected audit of unchanged candidate raw; v1 failure retained",
        "raw_sha256": sha256(raw_path),
        "exhaustive_states_checked": len(raw.get("exhaustive", [])),
        "kill_matrix": matrix,
        "errors": errors,
        "status": "PASS_T0_MUTATION_ADEQUACY" if not errors else "FAIL_AUDIT",
    }
    Path(output_path).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return output


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python audit_v2.py RAW.json AUDIT_V2.json")
    result = audit(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if not result["errors"] else 1)
