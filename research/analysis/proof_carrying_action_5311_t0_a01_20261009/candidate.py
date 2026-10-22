#!/usr/bin/env python3
"""Frozen finite-corpus candidate. Emits decisions, effect labels, and inspection counts."""
import hashlib, json, sys

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def full(plan, policy):
    count = 0; accepted = bool(plan.get("actions"))
    for action in plan.get("actions", []):
        for key in ("target", "epoch", "footprint", "lease_expires_at", "release_required"):
            count += 1
            expected = policy["lease_expires_at"] if key == "lease_expires_at" else policy[key]
            if key == "lease_expires_at":
                accepted &= policy["now"] <= action[key] <= expected
            else:
                accepted &= action[key] == expected
        accepted &= action["release_required"] is True
    return bool(accepted), count

def cert_check(case, policy):
    cert = case.get("certificate")
    if not cert or cert.get("plan_sha256") != digest(case["plan"]):
        return False, 1
    supported = set(policy["allowed_predicates"])
    if set(cert.get("predicates", [])) != set(policy["required_predicates"]):
        return False, 1
    count = 0; accepted = True
    # The checker must still validate every underlying action. The certificate
    # has no proof rule that soundly compresses these per-action obligations.
    for action in case["plan"].get("actions", []):
        for key in policy["required_predicates"]:
            count += 1
            expected = {"lease":cert.get("lease_expires_at"), "release":cert.get("release_required")}.get(key, cert.get(key))
            action_key = {"lease":"lease_expires_at", "release":"release_required"}.get(key, key)
            if key == "lease":
                accepted &= action[action_key] == expected and expected >= policy["now"]
            else:
                accepted &= action[action_key] == expected
    for key in policy["required_predicates"]:
        count += 1
        expected = {"lease":policy["lease_expires_at"], "release":policy["release_required"]}.get(key, policy.get(key))
        actual = {"lease":cert.get("lease_expires_at"), "release":cert.get("release_required")}.get(key, cert.get(key))
        if key == "lease": accepted &= actual >= policy["now"] and actual <= expected
        else: accepted &= actual == expected
    return bool(accepted), count + 2

def main(path, output):
    data=json.load(open(path)); rows=[]
    for case in data["cases"]:
        full_ok, full_cost=full(case["plan"], data["policy"])
        cert_ok, cert_cost=cert_check(case, data["policy"])
        rows.append({"id":case["id"],"full":{"admit":full_ok,"effect":case["expected_effect"] if full_ok else "not-dispatched","inspections":full_cost},"certificate":{"admit":cert_ok,"effect":case["expected_effect"] if cert_ok else "not-dispatched","inspections":cert_cost},"no_certificate":{"admit":False,"effect":"not-dispatched","inspections":0}})
    json.dump({"allocation":data["allocation"],"rows":rows},open(output,"w"),sort_keys=True,indent=2)
if __name__=="__main__": main(sys.argv[1],sys.argv[2])
