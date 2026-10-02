"""Independent raw-only oracle for Issue #6519; does not import candidate.py."""
import json
import sys
from pathlib import Path


def expected_valid(case, modes):
    card = case["card"]
    return (
        card["observation"] == case["observation"]
        and card["surface"] == case["surface"]
        and card["generation"] == case["generation"]
        and card["mode"] in modes
        and card["mode"] == case["raw_mode"]
    )


def audit(fixture, oracle, raw):
    by_case = {c["id"]: c for c in fixture["cases"]}
    oracle_cases = oracle["cases"]
    errors, caught, claim_disagreements = [], {}, []
    seen = set()
    expected_count = len(fixture["cases"]) * len(fixture["arms"])
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("arm"))
        if key in seen:
            errors.append({"kind": "duplicate_row", "key": key})
            continue
        seen.add(key)
        case = by_case.get(row.get("case_id"))
        truth = oracle_cases.get(row.get("case_id"))
        arm = row.get("arm")
        if case is None or truth is None or arm not in fixture["arms"]:
            errors.append({"kind": "unknown_row", "key": key})
            continue
        valid = expected_valid(case, fixture["supported_modes"])
        violations = []
        binding = row.get("binding", {})
        if row.get("raw_evidence_available") is not True:
            violations.append("raw_evidence_hidden")
        if row.get("authority") is not False:
            violations.append("authority_from_card")
        if row.get("completion") != "NONE":
            violations.append("completion_from_card")
        if row.get("goal_appropriateness") != "UNKNOWN":
            violations.append("goal_appropriateness_claimed")
        if row.get("effect_claim_status") != "UNVERIFIED":
            violations.append("effect_claim_promoted")
        if valid and arm != "RAW_ONLY":
            if binding != {"observation": case["observation"], "surface": case["surface"], "generation": case["generation"]}:
                violations.append("source_binding_lost")
            if row.get("mode") != case["raw_mode"]:
                violations.append("mode_mismatch")
            if arm == "FLIP_EFFECT_LABEL" and row.get("effect_claim") != truth["expected_effect"]:
                violations.append("effect_label_mismatch")
            if row.get("effect_claim") not in ("UNKNOWN", "NOT_EXPOSED") and row.get("effect_claim") != truth["expected_effect"]:
                claim_disagreements.append({"case_id": case["id"], "arm": arm, "claim": row.get("effect_claim"), "oracle": truth["expected_effect"], "status": row.get("effect_claim_status")})
            if arm in ("CANDIDATE_EFFECT", "UNCERTAINTY_CONTRADICTION", "DROP_SOURCE_BINDING", "FLIP_EFFECT_LABEL", "SUPPRESS_UNKNOWN", "CARD_AS_AUTHORITY", "HIDE_RAW_EVIDENCE") and row.get("operations") != case["card"]["operations"]:
                violations.append("operation_set_mismatch")
            if arm in ("CANDIDATE_EFFECT", "UNCERTAINTY_CONTRADICTION", "DROP_SOURCE_BINDING", "FLIP_EFFECT_LABEL", "SUPPRESS_UNKNOWN", "CARD_AS_AUTHORITY", "HIDE_RAW_EVIDENCE") and row.get("evidence_refs") != case["card"]["evidence"]:
                violations.append("evidence_ref_mismatch")
            if arm == "UNCERTAINTY_CONTRADICTION" and row.get("uncertainty") != "no_local_binding_or_mode_conflict_detected":
                violations.append("uncertainty_discarded")
        elif not valid and arm != "RAW_ONLY":
            if row.get("unknown") is not True:
                violations.append("unknown_suppressed")
            if row.get("mode") != "UNKNOWN" or row.get("operations") != [] or row.get("effect_claim") != "UNKNOWN":
                violations.append("invalid_card_exposed")
        mutant_expected = {
            "DROP_SOURCE_BINDING": "source_binding_lost",
            "FLIP_EFFECT_LABEL": "effect_label_mismatch",
            "SUPPRESS_UNKNOWN": "unknown_suppressed",
            "CARD_AS_AUTHORITY": "authority_from_card",
            "HIDE_RAW_EVIDENCE": "raw_evidence_hidden",
        }.get(arm)
        if mutant_expected:
            caught.setdefault(arm, 0)
            witnesses = {
                "DROP_SOURCE_BINDING": "current_genuine_modal",
                "FLIP_EFFECT_LABEL": "current_genuine_modal",
                "SUPPRESS_UNKNOWN": "modal_absent_old_card",
                "CARD_AS_AUTHORITY": "current_genuine_modal",
                "HIDE_RAW_EVIDENCE": "current_genuine_modal",
            }
            if case["id"] == witnesses[arm] and mutant_expected in violations:
                caught[arm] += 1
            elif case["id"] == witnesses[arm]:
                errors.append({"kind": "mutant_not_rejected", "case_id": case["id"], "arm": arm, "expected_violation": mutant_expected, "violations": violations})
        elif violations:
            errors.append({"kind": "canonical_invariant", "case_id": case["id"], "arm": arm, "violations": violations})
        if arm == "RAW_ONLY" and (row.get("mode") != "UNKNOWN" or row.get("operations") != [] or row.get("effect_claim") != "UNKNOWN" or row.get("evidence_refs") != []):
            errors.append({"kind": "raw_only_leak", "case_id": case["id"]})
    if len(seen) != expected_count:
        errors.append({"kind": "denominator_mismatch", "expected": expected_count, "observed": len(seen)})
    required_mutants = {"DROP_SOURCE_BINDING", "FLIP_EFFECT_LABEL", "SUPPRESS_UNKNOWN", "CARD_AS_AUTHORITY", "HIDE_RAW_EVIDENCE"}
    if set(caught) != required_mutants or any(v == 0 for v in caught.values()):
        errors.append({"kind": "mutation_coverage", "caught": caught, "required": sorted(required_mutants)})
    return {"schema": "issue-6519-t0-audit-v1", "status": "METHOD_PASS_SCOPED" if not errors else "FAIL_OR_STOP", "rows_expected": expected_count, "rows_seen": len(seen), "mutation_witness_counts": caught, "unverified_effect_claim_disagreements": claim_disagreements, "errors": errors}


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: auditor.py FIXTURE.json ORACLE.json CANDIDATE_RAW.json OUTPUT.json")
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    oracle = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    raw = json.loads(Path(argv[3]).read_text(encoding="utf-8"))
    result = audit(fixture, oracle, raw)
    Path(argv[4]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["status"], "errors", len(result["errors"]))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv)
