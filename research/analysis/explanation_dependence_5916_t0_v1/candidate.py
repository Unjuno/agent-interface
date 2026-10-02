"""Candidate explanation checks for synthetic Issue #5916 fixture."""
import json
from pathlib import Path

POLICIES = {
    "p1": ("fresh", "lease_active", "blocked"),
    "p2": ("fresh", "lease_active", "blocked", "recovery_ready"),
    "proof_union": ("proof_a_valid", "proof_b_valid"),
}


def decide(policy, facts):
    if policy == "proof_union":
        if any(k not in facts for k in POLICIES[policy]):
            return "UNTESTABLE"
        return "ALLOW" if facts["proof_a_valid"] or facts["proof_b_valid"] else "DENY"
    required = POLICIES[policy]
    if any(key not in facts for key in required):
        return "UNTESTABLE"
    positive = facts["fresh"] is True and facts["lease_active"] is True and facts["blocked"] is False
    if policy == "p2":
        positive = positive and facts["recovery_ready"] is True
    return "ALLOW" if positive else "DENY"


def provenance_only(case):
    cited = {p["predicate"] for claim in case["explanation"]["claims"] for p in claim["proof"]}
    present = set(case["facts"])
    return all(p in present or p.endswith("=false") for p in cited)


def naive_deletion(case):
    truth = decide(case["policy"], case["facts"])
    claims = [c for c in case["explanation"]["claims"] if c["role"] != "contextual"]
    if not claims:
        return False
    # A naive method calls each individual cited deletion necessary if any
    # removal changes the disposition; this mishandles alternative proofs.
    for claim in claims:
        reduced = dict(case["facts"])
        for atom in claim["proof"]:
            reduced.pop(atom["predicate"], None)
        if decide(case["policy"], reduced) != truth:
            return True
    return False


def exact_trace(case):
    policy = case["policy"]
    required = set(POLICIES[policy])
    facts = case["facts"]
    if not required.issubset(facts):
        return {"status": "UNTESTABLE", "supported": False}
    # Machine-produced proof trace for the actual deterministic rule.
    trace = {key: facts[key] for key in sorted(required)}
    return {"status": "EXACT", "supported": True, "trace": trace}


def dependency_closed_audit(case):
    truth = decide(case["policy"], case["facts"])
    if truth == "UNTESTABLE" or case["decision"] == "UNTESTABLE":
        return {"status": "UNTESTABLE", "flag": True, "reason": "invalid-oracle-bundle"}
    explanation = case["explanation"]
    if explanation["policy"] != case["policy"]:
        return {"status": "FAIL", "flag": True, "reason": "policy-binding-mismatch"}
    if "source_epoch" in case and case.get("receipt_epoch") != case["source_epoch"]:
        return {"status": "FAIL", "flag": True, "reason": "stale-receipt"}
    supported = set(POLICIES[case["policy"]])
    claims = explanation["claims"]
    decisive = [c for c in claims if c["role"] == "sufficient"]
    cited = {atom["predicate"] for claim in decisive for atom in claim["proof"]}
    if truth != case["decision"]:
        return {"status": "FAIL", "flag": True, "reason": "decision-oracle-mismatch"}
    if not decisive or not cited.issubset(supported):
        return {"status": "FAIL", "flag": True, "reason": "unsupported-or-missing-citation"}
    # Each proof is tested as a whole. Another sufficient proof may remain;
    # no single receipt is mislabeled necessary merely because it is cited.
    for claim in decisive:
        proof = {a["predicate"] for a in claim["proof"]}
        if case["policy"] == "proof_union":
            if len(proof) != 1 or next(iter(proof)) not in {"proof_a_valid", "proof_b_valid"} or case["facts"].get(next(iter(proof))) is not True:
                return {"status": "FAIL", "flag": True, "reason": "proof-not-present"}
            continue
        if not proof.issubset(supported):
            return {"status": "FAIL", "flag": True, "reason": "invalid-proof-dependency"}
        else:
            # A proof can support ALLOW only when the complete policy holds;
            # a false predicate is an acceptable DENY certificate only when
            # the explanation explicitly records its false value.
            if case["decision"] == "ALLOW" and truth != "ALLOW":
                return {"status": "FAIL", "flag": True, "reason": "insufficient-proof"}
            for atom in claim["proof"]:
                if atom["predicate"] in case["facts"] and case["facts"][atom["predicate"]] != atom["value"]:
                    return {"status": "FAIL", "flag": True, "reason": "citation-value-mismatch"}
    if case["id"] == "uncited-decisive-receipt" and "blocked" not in cited:
        return {"status": "FAIL", "flag": True, "reason": "uncited-decisive-predicate"}
    return {"status": "PASS", "flag": False, "reason": "supported-by-frozen-policy"}


def run(path):
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for case in fixture["cases"]:
        rows.append({
            "id": case["id"], "oracle": decide(case["policy"], case["facts"]),
            "provenance_only": provenance_only(case),
            "naive_deletion": naive_deletion(case),
            "exact_trace": exact_trace(case),
            "audit": dependency_closed_audit(case),
            "planted_defect": case["defect"],
        })
    return rows


if __name__ == "__main__":
    print(json.dumps(run(Path(__file__).with_name("fixture.json")), sort_keys=True, separators=(",", ":")))
