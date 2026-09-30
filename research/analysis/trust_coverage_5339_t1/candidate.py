"""Finite T1 discriminator for Issue #5339; standard library only."""
import hashlib
import json
from pathlib import Path


TRACES = [
    {"id": "trusted_single_positive", "expected": "PASS", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":True,"provenance":True,"scope":True}]},
    {"id": "trusted_single_negative", "expected": "FAIL", "e": [{"sign":"refute","fresh":True,"group":"g1","trusted":True,"provenance":True,"scope":True}]},
    {"id": "untrusted_single_positive", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":False,"provenance":True,"scope":True}]},
    {"id": "missing_provenance", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":True,"provenance":False,"scope":True}]},
    {"id": "duplicate_same_group", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":False,"provenance":True,"scope":True},{"sign":"support","fresh":True,"group":"g1","trusted":False,"provenance":True,"scope":True}]},
    {"id": "correlated_distinct_labels", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"shared-source","trusted":False,"provenance":True,"scope":True},{"sign":"support","fresh":True,"group":"shared-source","trusted":False,"provenance":True,"scope":True}]},
    {"id": "independent_two_positive", "expected": "PASS", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":False,"provenance":True,"scope":True},{"sign":"support","fresh":True,"group":"g2","trusted":False,"provenance":True,"scope":True}]},
    {"id": "stale_plus_trusted_current", "expected": "PASS", "e": [{"sign":"support","fresh":False,"group":"g0","trusted":True,"provenance":True,"scope":True},{"sign":"support","fresh":True,"group":"g1","trusted":True,"provenance":True,"scope":True}]},
    {"id": "stale_only", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":False,"group":"g1","trusted":True,"provenance":True,"scope":True}]},
    {"id": "scope_mismatch_only", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":True,"provenance":True,"scope":False}]},
    {"id": "trusted_conflict", "expected": "ABSTAIN", "e": [{"sign":"support","fresh":True,"group":"g1","trusted":True,"provenance":True,"scope":True},{"sign":"refute","fresh":True,"group":"g2","trusted":True,"provenance":True,"scope":True}]},
]


def decide(trace, policy):
    valid = [e for e in trace["e"] if e["fresh"] and e["provenance"] and e["scope"]]
    supports = {e["group"] for e in valid if e["sign"] == "support"}
    refutes = {e["group"] for e in valid if e["sign"] == "refute"}
    if supports and refutes:
        return "ABSTAIN"
    groups = supports or refutes
    if not groups:
        return "ABSTAIN"
    if policy == "two_group":
        if len(groups) < 2:
            return "ABSTAIN"
    elif policy == "contract_singleton":
        if len(groups) == 1 and not all(e["trusted"] for e in valid if e["group"] in groups):
            return "ABSTAIN"
    elif policy != "any_singleton":
        raise ValueError(policy)
    return "PASS" if supports else "FAIL"


def main():
    rows = []
    for t in TRACES:
        rows.append({"id": t["id"], "expected": t["expected"], "two_group": decide(t,"two_group"),
                     "contract_singleton": decide(t,"contract_singleton"), "any_singleton": decide(t,"any_singleton")})
    payload = {"schema":"trust-coverage-5339-t1-v1", "trace_count":len(rows), "rows":rows}
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":"))+"\n").encode()
    d=Path(__file__).parent
    (d/"raw.json").write_bytes(raw)
    (d/"raw.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  raw.json\n")
    print(json.dumps({"status":"CANDIDATE_COMPLETE","trace_count":len(rows),"raw_sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))


if __name__ == "__main__":
    main()
