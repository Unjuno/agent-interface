"""Corrected decision-label audit; re-reads raw inputs without the validator."""
import hashlib
import json
from pathlib import Path

from audit import independent_error, KNOWN_PRIMITIVES

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "verification_ir_5268_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw_path = Path("/out/RAW-01.json")
    raw = json.loads(raw_path.read_text())
    formal = json.loads((PARENT / "FORMAL-01.json").read_text())
    oracle = json.loads((PARENT / "oracle_expected.json").read_text())
    names = ("check_id", "primitive", "subject_ref", "criticality",
             "required_evidence_role", "verifier_class", "dependencies")
    raw_cases = {case["case_id"]: case for case in raw["cases"]}
    formal_cases = {case["case_id"]: case for case in formal["cases"]}
    input_integrity = (
        raw["parent_allocation"] == formal["allocation"] and
        raw["parent_formal_sha256"] == sha(PARENT / "FORMAL-01.json") and
        raw["parent_oracle_sha256"] == sha(PARENT / "oracle_expected.json")
    )
    oracle_match = set(raw_cases) == set(formal_cases) == set(oracle)
    for case_id, case in raw_cases.items():
        rows = [tuple(check[field] for field in names)
                for check in case["required_ir"]["checks"]]
        oracle_match &= case["action"] == formal_cases[case_id]["action"]
        oracle_match &= case["oracle_match"] is True and rows == [tuple(row) for row in oracle[case_id]]

    omission_expected = {
        (case_id, check["check_id"])
        for case_id, case in raw_cases.items()
        for check in case["required_ir"]["checks"]
        if check["criticality"] != "OPTIONAL"
    }
    omission_observed = set()
    for attempt in raw["attempts"]:
        if attempt["id"].startswith("omit/"):
            _, case_id, check_id = attempt["id"].split("/", 2)
            omission_observed.add((case_id, check_id))

    disagreements = []
    decisions = {"ACCEPT": 0, "REJECT": 0}
    for attempt in raw["attempts"]:
        rejection_reason = independent_error(
            attempt["required_ir"], attempt["proposed_ir"], attempt["profiles"])
        expected_observed = "REJECT" if rejection_reason else "ACCEPT"
        decisions[expected_observed] += 1
        if (attempt["expected"] != expected_observed or
                attempt["observed"] != expected_observed):
            disagreements.append({"id": attempt["id"], "expected": attempt["expected"],
                                  "observed": attempt["observed"],
                                  "independent": expected_observed})
        if "authority" in attempt["detail"] or "verdict" in attempt["detail"]:
            disagreements.append({"id": attempt["id"], "issue": "truth_or_authority_field"})

    high = next(attempt for attempt in raw["attempts"]
                if attempt["id"] == "corrupt/high-risk-effect-safeguards-omitted")
    effects = [row for row in high["required_ir"]["checks"]
               if row["primitive"].startswith("EFFECT.")]
    high_proxy_ok = (
        formal_cases["external-side-effect"]["action"]["external_side_effect"] is True and
        len(effects) == 2 and high["observed"] == "REJECT" and
        all(row["check_id"] not in {x["check_id"] for x in high["proposed_ir"]["checks"]}
            for row in effects)
    )
    escalation_present = any("ESCALAT" in primitive for primitive in KNOWN_PRIMITIVES)
    checks = {
        "input_integrity": input_integrity,
        "exact_case_set_and_parent_oracle": oracle_match,
        "every_mandatory_row_omission_attempted": omission_expected == omission_observed,
        "all_attempts_match_independent_decisions": not disagreements,
        "external_side_effect_proxy_rejects_missing_safeguards": high_proxy_ok,
        "accepted_outputs_make_no_truth_or_authority_claim": not disagreements,
        "frozen_ontology_encodes_required_risk_escalation": escalation_present,
    }
    core_gates = all(value for name, value in checks.items()
                     if name != "frozen_ontology_encodes_required_risk_escalation")
    previous = json.loads(Path("/out/AUDIT-01.json").read_text())
    prior_label_corrected = (
        previous["disposition"] == "FAIL_AUDIT_DISAGREEMENT" and
        previous["checks"] == {
            "all_attempts_authority_neutral": True,
            "case_set_exact": True,
            "every_mandatory_row_has_omission_control": True,
            "frozen_ontology_encodes_risk_escalation": False,
            "high_consequence_proxy_rejects_missing_effect_safeguards": True,
            "independent_attempt_decisions_match": True,
            "input_hashes_match": True,
            "required_policy_matches_frozen_oracle": True,
        }
    )
    disposition = ("FAIL_AUDIT_DISAGREEMENT" if not core_gates else
                   "HOLD_UNREPRESENTED_RISK_ESCALATION" if not escalation_present else
                   "PASS_SCOPED")
    result = {
        "schema": "verification_coverage_5269_corrected_audit.v1",
        "raw_sha256": sha(raw_path), "audit_01_sha256": sha(Path("/out/AUDIT-01.json")),
        "auditor_source_sha256": sha(HERE / "audit_v2.py"),
        "checks": checks, "attempt_decisions": decisions,
        "attempt_disagreements": disagreements,
        "prior_audit_classification_bug_confirmed": prior_label_corrected,
        "disposition": disposition,
    }
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path("/out/AUDIT-02.json").write_text(encoded)
    print(json.dumps({"disposition": disposition, "checks": checks,
                      "decisions": decisions, "disagreements": len(disagreements),
                      "prior_audit_classification_bug_confirmed": prior_label_corrected,
                      "audit_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
