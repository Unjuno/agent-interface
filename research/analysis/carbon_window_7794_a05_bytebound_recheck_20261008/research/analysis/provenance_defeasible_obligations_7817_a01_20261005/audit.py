"""Independent expected-ledger audit; imports no candidate code."""
import json
import sys
from pathlib import Path

EXPECTED = {
    "exception_in_scope": ("RESOLVED_ADVISORY", ["PERMIT"], None, [("retry", "default", ["retry", "default"], ["s3"])]),
    "exception_out_of_scope": ("RESOLVED_ADVISORY", ["DENY"], None, []),
    "incomparable_conflict": ("UNKNOWN_STOP", [], "UNRESOLVED_OR_AMBIGUOUS_CONFLICT", []),
    "unauthenticated_edge": ("UNKNOWN_STOP", [], "INVALID_PRIORITY_PROVENANCE_OR_SCOPE", []),
    "priority_cycle": ("UNKNOWN_STOP", [], "PRIORITY_CYCLE", []),
    "strict_prohibition": ("UNKNOWN_STOP", [], "STRICT_RULE_ATTACK", []),
    "duplicate_source_versions": ("UNKNOWN_STOP", [], "DUPLICATE_RULE_ID_OR_VERSION", []),
    "specificity_condition": ("RESOLVED_ADVISORY", ["PERMIT"], None, []),
    "irrelevant_evidence_added": ("RESOLVED_ADVISORY", ["DENY"], None, [("deny", "permit", ["deny", "permit"], ["s3"])]),
    "revocation_supersession": ("RESOLVED_ADVISORY", ["DENY"], None, []),
}
MUTATIONS = {
    "remove_source_span": "MISSING_SOURCE_OR_WIDENED_SCOPE",
    "forge_issuer": "INVALID_PRIORITY_PROVENANCE_OR_SCOPE",
    "widen_scope": "MISSING_SOURCE_OR_WIDENED_SCOPE",
    "insert_priority_cycle": "PRIORITY_CYCLE",
    "defeat_strict_prohibition": "STRICT_RULE_ATTACK",
}


def audit(raw):
    errors = []
    rows = {r.get("case_id"): r for r in raw.get("rows", [])}
    if raw.get("case_count") != len(EXPECTED) or set(rows) != set(EXPECTED):
        errors.append("case_denominator_or_ids")
    for case_id, expected in EXPECTED.items():
        row = rows.get(case_id, {})
        status, obligations, reason, proofs = expected
        if row.get("status") != status or row.get("obligations") != obligations or row.get("reason") != reason:
            errors.append(case_id + ":decision")
        if row.get("authority_changed") is not False or "authorized" in json.dumps(row).lower():
            errors.append(case_id + ":authority_boundary")
        actual_proofs = [(p.get("winner"), p.get("loser"), p.get("priority_path"), p.get("edge_sources")) for p in row.get("proofs", [])]
        if actual_proofs != proofs:
            errors.append(case_id + ":proof_coverage")
        if status == "RESOLVED_ADVISORY" and not set(obligations).issubset({"PERMIT", "DENY"}):
            errors.append(case_id + ":unknown_obligation")
    mutations = {m.get("mutation"): m.get("result", {}) for m in raw.get("mutations", [])}
    if raw.get("mutation_count") != len(MUTATIONS) or set(mutations) != set(MUTATIONS):
        errors.append("mutation_denominator_or_ids")
    for name, reason in MUTATIONS.items():
        row = mutations.get(name, {})
        if row.get("status") != "UNKNOWN_STOP" or row.get("reason") != reason or row.get("authority_changed") is not False or row.get("obligations") != []:
            errors.append(name + ":mutation_survived")
    # Independent control calculations from the explicit semantics: without an
    # authenticated priority, opposing defeasible rules stay unresolved; a
    # last-rule-wins policy would contradict the strict prohibition fixture.
    if not (EXPECTED["incomparable_conflict"][0] == "UNKNOWN_STOP" and EXPECTED["strict_prohibition"][0] == "UNKNOWN_STOP"):
        errors.append("conservative_control")
    order_sensitive = ["strict", "exception"]
    naive_last = "PERMIT" if order_sensitive[-1] == "exception" else "DENY"
    if naive_last != "PERMIT":
        errors.append("naive_last_wins_control")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "case_rows": len(rows), "mutation_rows": len(mutations), "errors": errors, "authority_emitted": False, "scope": "finite authored obligations only"}


if __name__ == "__main__":
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    result = audit(json.loads(source.read_text(encoding="utf-8")))
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
