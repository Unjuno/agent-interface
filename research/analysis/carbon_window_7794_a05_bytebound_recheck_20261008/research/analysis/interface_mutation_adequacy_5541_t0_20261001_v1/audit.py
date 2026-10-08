"""Independent raw-only mutation-adequacy auditor; does not import candidate.py."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specification(state):
    return (state["evidence_present"] and state["evidence_fresh"]
            and state["authority_matches"] and state["outcome_known"]
            and not state["terminal_failure"])


def mutation_semantics(state, operator):
    if (operator == "compound_provenance_authority_terminal"
            and state["evidence_present"] is False
            and state["authority_matches"] is False
            and state["terminal_failure"] is True):
        return True
    required = {
        "drop_provenance": ("evidence_fresh", "authority_matches", "outcome_known"),
        "accept_stale": ("evidence_present", "authority_matches", "outcome_known"),
        "ignore_authority": ("evidence_present", "evidence_fresh", "outcome_known"),
        "commit_unknown": ("evidence_present", "evidence_fresh", "authority_matches"),
        "reactivate_terminal": ("evidence_present", "evidence_fresh",
                                "authority_matches", "outcome_known"),
        "compound_provenance_authority_terminal": FIELDS,
    }[operator]
    return all(state[field] for field in required)


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
        tuple(state[k] for k in KEYS)
        for state in (dict(zip(KEYS, values))
                      for values in itertools.product((False, True), repeat=len(KEYS)))
    }
    actual_states = {
        tuple(row["state"].get(k) for k in KEYS) for row in raw.get("exhaustive", [])
    }
    if actual_states != expected_states or len(raw.get("exhaustive", [])) != 32:
        errors.append("exhaustive_state_inventory_incomplete_or_duplicate")

    mutant_results = {
        name: {"baseline_killed": False, "metamorphic_killed": False,
               "independent_oracle_killed": False}
        for name in MUTANTS
    }
    baseline_expectations = {
        "nominal_commit": True,
        "missing_provenance": False,
        "unknown_outcome": False,
    }
    baseline_rows = {row["case"]: row for row in raw.get("baseline", [])}
    if set(baseline_rows) != set(baseline_expectations):
        errors.append("baseline_inventory_mismatch")
    for case, expected in baseline_expectations.items():
        row = baseline_rows.get(case)
        if not row:
            continue
        if row.get("expected_commit") is not expected or specification(row["state"]) is not expected:
            errors.append(f"baseline_spec_mismatch:{case}")
        decisions = row.get("decisions", {})
        if decisions.get("candidate") is not expected:
            errors.append(f"candidate_baseline_mismatch:{case}")
        for name in MUTANTS:
            if decisions.get(name) is not expected:
                mutant_results[name]["baseline_killed"] = True

    expected_relations = {
        "degrade_evidence_fresh_must_not_commit": ("evidence_fresh", False),
        "degrade_authority_matches_must_not_commit": ("authority_matches", False),
        "degrade_terminal_failure_must_not_commit": ("terminal_failure", True),
    }
    meta_rows = {row["relation"]: row for row in raw.get("metamorphic", [])}
    if set(meta_rows) != set(expected_relations):
        errors.append("metamorphic_inventory_mismatch")
    for relation, (field, degraded_value) in expected_relations.items():
        row = meta_rows.get(relation)
        if not row:
            continue
        base, degraded = row["base_state"], row["degraded_state"]
        if (base[field] is not True or degraded[field] is not degraded_value
                or not specification(base) or specification(degraded)):
            errors.append(f"metamorphic_spec_mismatch:{relation}")
        if row.get("base_decisions", {}).get("candidate") is not True:
            errors.append(f"candidate_metamorphic_base_mismatch:{relation}")
        degraded_decisions = row.get("degraded_decisions", {})
        if degraded_decisions.get("candidate") is not False:
            errors.append(f"candidate_metamorphic_degraded_mismatch:{relation}")
        for name in MUTANTS:
            if degraded_decisions.get(name) is not False:
                mutant_results[name]["metamorphic_killed"] = True

    for row in raw.get("exhaustive", []):
        state = row["state"]
        decisions = row.get("decisions", {})
        expected = specification(state)
        if decisions.get("candidate") is not expected:
            errors.append(f"candidate_exhaustive_mismatch:{tuple(state[k] for k in KEYS)}")
        for name in MUTANTS:
            semantic = mutation_semantics(state, name)
            if decisions.get(name) is not semantic:
                errors.append(f"mutant_semantics_mismatch:{name}:{tuple(state[k] for k in KEYS)}")
            if semantic is not expected:
                mutant_results[name]["independent_oracle_killed"] = True

    for name, result in mutant_results.items():
        result["non_equivalent"] = result["independent_oracle_killed"]
        result["killed_by_declared_oracles"] = (
            result["baseline_killed"] or result["metamorphic_killed"]
            or result["independent_oracle_killed"]
        )
        if not result["killed_by_declared_oracles"]:
            errors.append(f"surviving_non_equivalent_mutant:{name}")

    outcome = {
        "schema": "issue5541-mutation-adequacy-audit-v1",
        "raw_sha256": sha256(raw_path),
        "exhaustive_states_checked": len(raw.get("exhaustive", [])),
        "mutants": mutant_results,
        "errors": errors,
        "status": "PASS_T0_MUTATION_ADEQUACY" if not errors else "FAIL_AUDIT",
    }
    Path(output_path).write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    return outcome


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python audit.py RAW.json OUTPUT.json")
    result = audit(sys.argv[1], sys.argv[2])
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
