"""Independent truth-table and output auditor; imports no candidate code."""
import json
import sys
from pathlib import Path

RULES = {
    "p1": ("fresh", "lease_active", "blocked"),
    "p2": ("fresh", "lease_active", "blocked", "recovery_ready"),
    "proof_union": ("proof_a_valid", "proof_b_valid"),
}


def reference(policy, facts):
    keys = RULES.get(policy)
    if keys is None or any(k not in facts for k in keys):
        return "UNTESTABLE"
    if policy == "proof_union":
        return "ALLOW" if facts["proof_a_valid"] or facts["proof_b_valid"] else "DENY"
    allowed = facts["fresh"] is True and facts["lease_active"] is True and facts["blocked"] is False
    if policy == "p2":
        allowed = allowed and facts["recovery_ready"] is True
    return "ALLOW" if allowed else "DENY"


def independently_assess(case, candidate_row):
    truth = reference(case["policy"], case["facts"])
    expected_defect = case["defect"]
    issues = []
    exp = case["explanation"]
    if truth != case["decision"] and case["decision"] != "UNTESTABLE":
        issues.append("declared-decision-does-not-follow-policy")
    if exp["policy"] != case["policy"] and candidate_row["audit"]["reason"] != "policy-binding-mismatch":
        issues.append("policy-identity-mismatch")
    if "source_epoch" in case and case.get("receipt_epoch") != case["source_epoch"] and candidate_row["audit"]["reason"] != "stale-receipt":
        issues.append("stale-cited-receipt")
    if case.get("perturbation", {}).get("dependency_closed") is False and candidate_row["audit"]["status"] != "UNTESTABLE":
        issues.append("illegal-counterfactual")
    if "source_epoch" in case and case.get("receipt_epoch") != case["source_epoch"] and candidate_row["audit"]["reason"] == "stale-receipt" and not candidate_row["audit"]["flag"]:
        issues.append("stale-receipt-not-flagged")
    sufficient = [c for c in exp["claims"] if c["role"] == "sufficient"]
    recognized = set(RULES.get(case["policy"], ()))
    cited = {x["predicate"] for c in sufficient for x in c["proof"]}
    if not sufficient and case["decision"] != "UNTESTABLE":
        issues.append("no-decision-reason")
    if case["id"] == "uncited-decisive-receipt" and "blocked" not in cited:
        issues.append("decisive-fact-not-cited")
    if case["id"] == "redundant-independent-proofs":
        proofs = [{x["predicate"] for x in c["proof"]} for c in sufficient]
        if len(proofs) != 2 or proofs[0] == proofs[1] or \
                not case["facts"].get("proof_a_valid") or not case["facts"].get("proof_b_valid"):
            issues.append("alternative-proof-set-lost")
    if any(x["predicate"] not in recognized and x["predicate"] not in {"proof_a_valid", "proof_b_valid"}
           for c in sufficient for x in c["proof"]):
        issues.append("claim-not-bound-to-rule-predicate")
    if case["id"] == "policy-swap-stale-explanation" and exp["policy"] == case["policy"]:
        raise AssertionError("frozen policy-swap control is not a mismatch")
    if case["id"] == "redundant-independent-proofs":
        # The exact trace is machine-produced directly from the frozen policy
        # and is an authority-equivalent stronger baseline than the audit.
        if candidate_row["exact_trace"]["trace"] != {
                "proof_a_valid": True, "proof_b_valid": True}:
            issues.append("exact-trace-does-not-reconstruct-redundant-decision")
    if case["id"] == "context-only-citation" and "window_title" in cited:
        issues.append("context-promoted-to-decisive-citation")
    flagged = bool(candidate_row["audit"]["flag"])
    if expected_defect and not flagged:
        issues.append("planted-defect-missed")
    if not expected_defect and flagged:
        issues.append("valid-case-falsely-flagged")
    if candidate_row["oracle"] != truth:
        issues.append("candidate-oracle-disagrees")
    return {"id": case["id"], "truth": truth, "expected_defect": expected_defect,
            "candidate_flag": flagged, "issues": issues}


def main():
    root = Path(__file__).parent
    cases = json.loads((root / "fixture.json").read_text(encoding="utf-8"))["cases"]
    rows = json.loads((root / "candidate_output.json").read_text(encoding="utf-8"))
    if len(rows) != len(cases) or [x["id"] for x in rows] != [x["id"] for x in cases]:
        raise SystemExit("row cardinality/order mismatch")
    assessments = [independently_assess(c, r) for c, r in zip(cases, rows)]
    errors = [e for row in assessments for e in row["issues"]]
    result = {"auditor": "independent-truth-table-v1", "rows": assessments,
              "error_count": len(errors), "errors": errors,
              "controls": {"invalid_deletion_untestable": any(
                  c["id"] == "invalid-mandatory-deletion" and
                  r["oracle"] == "UNTESTABLE" and r["audit"]["status"] == "UNTESTABLE"
                  for c, r in zip(cases, rows)),
                  "redundant_proofs_accepted": not any(
                  "alternative-proof-set-lost" in e["issues"] for e in assessments),
                  "exact_trace_covers_policy_decision": not any(
                  "exact-trace-does-not-reconstruct-redundant-decision" in e["issues"]
                  for e in assessments),
                  "stale_policy_detected": any(
                  c["id"] == "policy-swap-stale-explanation" and
                  r["audit"]["reason"] == "policy-binding-mismatch" and r["audit"]["flag"]
                  for c, r, a in zip(cases, rows, assessments)),
                  "uncited_decisive_detected": any(
                  c["id"] == "uncited-decisive-receipt" and r["audit"]["flag"]
                  for c, r in zip(cases, rows))}}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if errors or not all(result["controls"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
