"""Independent raw-only audit. Deliberately does not import candidate.py."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "disjoint_commuting": {"divergent": False, "declared_conflict": False, "decision": "PARALLEL"},
    "same_key_add": {"divergent": False, "declared_conflict": True, "decision": "SERIALIZE"},
    "read_write_order": {"divergent": True, "declared_conflict": True, "decision": "SERIALIZE"},
    "hidden_read": {"divergent": True, "declared_conflict": False, "decision": "PARALLEL"},
    "unknown_footprint": {"divergent": False, "declared_conflict": False, "decision": "UNCERTAIN"},
}


def invalid_reasons(raw: dict) -> list[str]:
    errors = []
    if raw.get("schema") != "semantic-serializability-raw-v1":
        errors.append("schema")
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != 5:
        return errors + ["row_count"]
    seen = set()
    for row in rows:
        name = row.get("case")
        if name not in EXPECTED or name in seen:
            errors.append("case_identity")
            continue
        seen.add(name)
        expected = EXPECTED[name]
        divergent = expected["divergent"]
        semantic_decision = expected["decision"]
        policies = row.get("policies", {})
        if policies.get("RAW_COALESCE", {}).get("decision") != "PARALLEL":
            errors.append(name + ":raw_decision")
        if policies.get("RAW_COALESCE", {}).get("serial_outcome_divergence") is not divergent:
            errors.append(name + ":raw_effect")
        if policies.get("GLOBAL_SERIAL", {}).get("decision") != "SERIALIZE":
            errors.append(name + ":global")
        semantic = policies.get("SEMANTIC_GATE", {})
        expected_decision = semantic_decision
        expected_conflict = bool(expected_decision == "PARALLEL" and divergent)
        if (semantic.get("decision") != expected_decision or
                semantic.get("serial_outcome_divergence") is not expected_conflict):
            errors.append(name + ":semantic")
        oracle = row.get("oracle", {})
        outcomes = oracle.get("legal_serial_outcomes", [])
        observed = oracle.get("observed_concurrent_outcome")
        independently_matches = observed in outcomes
        if oracle.get("concurrent_matches_serial") is not independently_matches:
            errors.append(name + ":oracle_conflict")
        if oracle.get("declared_read_write_conflict") is not expected["declared_conflict"]:
            errors.append(name + ":declared_conflict")
        if len(oracle.get("legal_serial_outcomes", [])) != 2:
            errors.append(name + ":serial_outcomes")
        if row.get("metrics", {}).get("global_parallel_pairs") != 0:
            errors.append(name + ":global_metric")
    if seen != set(EXPECTED):
        errors.append("case_set")
    if raw.get("authority_grants") != 0 or raw.get("external_effects") != 0:
        errors.append("authority_or_effects")
    return errors


def main(source: str, raw_path: str, audit_path: str) -> None:
    raw_bytes = Path(raw_path).read_bytes()
    raw = json.loads(raw_bytes)
    baseline = invalid_reasons(raw)
    controls = {}
    mutations = {
        "drop_case": lambda x: x["cases"].pop(),
        "flip_raw": lambda x: x["cases"][1]["policies"]["RAW_COALESCE"].update(decision="SERIALIZE"),
        "claim_hidden_read_caught": lambda x: x["cases"][3]["policies"]["SEMANTIC_GATE"].update(serial_outcome_divergence=False),
        "alter_concurrent_state": lambda x: x["cases"][3]["oracle"].update(observed_concurrent_outcome={"y": 99}),
        "authority_grant": lambda x: x.update(authority_grants=1),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls[name] = bool(invalid_reasons(changed))
    result = {
        "schema": "semantic-serializability-audit-v1",
        "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "errors": baseline,
        "mutation_controls_rejected": controls,
        "disposition": "PASS_CONSTRUCTION_SCOPED" if not baseline and all(controls.values()) else "FAIL_AUDIT",
        "scope": "five hand-authored synthetic cases; declared footprint cannot detect omitted hidden read",
    }
    Path(audit_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:])
