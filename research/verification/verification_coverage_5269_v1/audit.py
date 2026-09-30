"""Independent raw-output auditor; imports neither candidate nor coverage."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "verification_ir_5268_v1"
KNOWN_PRIMITIVES = {
    "TARGET.IDENTITY_CURRENT", "TARGET.TARGET_MATCH", "TARGET.AMBIGUITY",
    "SEMANTIC.INTENT_MATCH", "SEMANTIC.SCOPE_MATCH",
    "AUTHORITY.PERMISSION_CURRENT", "AUTHORITY.DECISION_DEADLINE",
    "EFFECT.REVERSIBILITY", "EFFECT.POSTCONDITION", "META.UNKNOWN_REQUIRED",
    "META.COVERAGE",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_error(required_ir, proposed_ir, profiles):
    if set(required_ir) != {"schema", "unknown_check_required", "checks"}:
        return "required-schema"
    if set(proposed_ir) != {"schema", "unknown_check_required", "checks"}:
        return "proposed-schema"
    if required_ir["schema"] != "verification_ir.v0.1" or proposed_ir["schema"] != "verification_ir.v0.1":
        return "schema-version"
    required = {row["check_id"]: row for row in required_ir["checks"]
                if row["criticality"] != "OPTIONAL"}
    proposed = {row["check_id"]: row for row in proposed_ir["checks"]}
    if not set(required).issubset(proposed):
        return "missing-mandatory"
    if any(proposed[key] != row for key, row in required.items()):
        return "changed-mandatory-contract"
    if any(row["criticality"] != "OPTIONAL" for key, row in proposed.items()
           if key not in required):
        return "extra-nonoptional"
    seen = set()
    seen_ids = set()
    for row in proposed_ir["checks"]:
        if row["primitive"] not in KNOWN_PRIMITIVES:
            return "unknown-primitive"
        if row["check_id"] in seen_ids:
            return "duplicate-id"
        seen_ids.add(row["check_id"])
        semantic = (row["primitive"], row["subject_ref"], row["required_evidence_role"])
        if semantic in seen:
            return "duplicate-semantic-check"
        seen.add(semantic)
        deadline = row["deadline"]
        if deadline is not None:
            profile = profiles.get(row["verifier_class"])
            if not isinstance(profile, dict):
                return "missing-verifier-profile"
            bound = profile.get("upper_bound_ms")
            if type(bound) is not int or bound < 0:
                return "invalid-verifier-profile"
            if bound > deadline:
                return "deadline-infeasible"
    return None


def main():
    raw = json.loads(Path("/out/RAW-01.json").read_text())
    formal = json.loads((PARENT / "FORMAL-01.json").read_text())
    oracle = json.loads((PARENT / "oracle_expected.json").read_text())
    field_names = ("check_id", "primitive", "subject_ref", "criticality",
                   "required_evidence_role", "verifier_class", "dependencies")
    raw_cases = {row["case_id"]: row for row in raw["cases"]}
    formal_cases = {row["case_id"]: row for row in formal["cases"]}
    checks = {}
    checks["input_hashes_match"] = (
        raw["parent_formal_sha256"] == sha(PARENT / "FORMAL-01.json") and
        raw["parent_oracle_sha256"] == sha(PARENT / "oracle_expected.json") and
        raw["parent_allocation"] == formal["allocation"])
    checks["case_set_exact"] = set(raw_cases) == set(formal_cases) == set(oracle)
    oracle_matches = True
    for case_id, item in raw_cases.items():
        expected = [tuple(values) for values in oracle[case_id]]
        observed = [tuple(check[key] for key in field_names)
                    for check in item["required_ir"]["checks"]]
        oracle_matches &= item["oracle_match"] is True and observed == expected
        oracle_matches &= item["action"] == formal_cases[case_id]["action"]
    checks["required_policy_matches_frozen_oracle"] = oracle_matches

    expected_omissions = {
        (case_id, row["check_id"])
        for case_id, item in raw_cases.items()
        for row in item["required_ir"]["checks"]
        if row["criticality"] != "OPTIONAL"
    }
    observed_omissions = set()
    for attempt in raw["attempts"]:
        if attempt["id"].startswith("omit/"):
            _, case_id, check_id = attempt["id"].split("/", 2)
            observed_omissions.add((case_id, check_id))
    checks["every_mandatory_row_has_omission_control"] = observed_omissions == expected_omissions

    attempts_correct = True
    independently_accepted = 0
    error_kinds = {}
    for attempt in raw["attempts"]:
        error = independent_error(attempt["required_ir"], attempt["proposed_ir"],
                                  attempt["profiles"])
        accepted = error is None
        independently_accepted += int(accepted)
        if error:
            error_kinds[error] = error_kinds.get(error, 0) + 1
        attempts_correct &= accepted == (attempt["expected"] == "ACCEPT")
        attempts_correct &= accepted == (attempt["observed"] == "ACCEPT")
        attempts_correct &= "authority" not in attempt["detail"]
        attempts_correct &= "verdict" not in attempt["detail"]
    checks["independent_attempt_decisions_match"] = attempts_correct

    ext_action = formal_cases["external-side-effect"]["action"]
    ext_attempt = next(a for a in raw["attempts"]
                       if a["id"] == "corrupt/high-risk-effect-safeguards-omitted")
    required_effects = [row for row in ext_attempt["required_ir"]["checks"]
                        if row["primitive"].startswith("EFFECT.")]
    checks["high_consequence_proxy_rejects_missing_effect_safeguards"] = (
        ext_action["external_side_effect"] is True and len(required_effects) == 2 and
        all(row["check_id"] not in {x["check_id"] for x in ext_attempt["proposed_ir"]["checks"]}
            for row in required_effects) and ext_attempt["observed"] == "REJECT")
    checks["frozen_ontology_encodes_risk_escalation"] = any(
        "ESCALAT" in primitive for primitive in KNOWN_PRIMITIVES)
    checks["all_attempts_authority_neutral"] = all(
        "authority" not in attempt["detail"] and "verdict" not in attempt["detail"]
        for attempt in raw["attempts"] if attempt["observed"] == "ACCEPT")

    complete = all(checks.values())
    audit = {
        "schema": "verification_coverage_5269_audit.v1",
        "raw_sha256": sha(Path("/out/RAW-01.json")),
        "parent_formal_sha256": sha(PARENT / "FORMAL-01.json"),
        "parent_oracle_sha256": sha(PARENT / "oracle_expected.json"),
        "checks": checks,
        "counts": {"cases": len(raw_cases), "attempts": len(raw["attempts"]),
                   "independently_accepted": independently_accepted,
                   "independently_rejected": len(raw["attempts"]) - independently_accepted,
                   "omission_controls": len(observed_omissions),
                   "error_kinds": error_kinds},
        "disposition": ("HOLD_UNREPRESENTED_RISK_ESCALATION" if complete and
                        not checks["frozen_ontology_encodes_risk_escalation"]
                        else "PASS_SCOPED" if complete else "FAIL_AUDIT_DISAGREEMENT"),
    }
    encoded = json.dumps(audit, sort_keys=True, indent=2) + "\n"
    Path("/out/AUDIT-01.json").write_text(encoded)
    print(json.dumps({"disposition": audit["disposition"], "checks": checks,
                      "counts": audit["counts"],
                      "audit_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
