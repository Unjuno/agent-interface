"""Independent raw-only audit: does not import candidate.py."""
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "trusted_single_positive": ("ABSTAIN", "PASS", "PASS"),
    "trusted_single_negative": ("ABSTAIN", "FAIL", "FAIL"),
    "untrusted_single_positive": ("ABSTAIN", "ABSTAIN", "PASS"),
    "missing_provenance": ("ABSTAIN", "ABSTAIN", "ABSTAIN"),
    "duplicate_same_group": ("ABSTAIN", "ABSTAIN", "PASS"),
    "correlated_distinct_labels": ("ABSTAIN", "ABSTAIN", "PASS"),
    "independent_two_positive": ("PASS", "PASS", "PASS"),
    "stale_plus_trusted_current": ("ABSTAIN", "PASS", "PASS"),
    "stale_only": ("ABSTAIN", "ABSTAIN", "ABSTAIN"),
    "scope_mismatch_only": ("ABSTAIN", "ABSTAIN", "ABSTAIN"),
    "trusted_conflict": ("ABSTAIN", "ABSTAIN", "ABSTAIN"),
}


def main():
    d=Path(__file__).parent
    raw=(d/"raw.json").read_bytes()
    data=json.loads(raw)
    rows=data["rows"]
    errors=[]
    if data.get("schema")!="trust-coverage-5339-t1-v1" or len(rows)!=11 or len(EXPECTED)!=11:
        errors.append("shape")
    if len({r["id"] for r in rows})!=11:
        errors.append("duplicate_or_missing_trace")
    for r in rows:
        exp=EXPECTED.get(r["id"])
        # Any-singleton is a deliberately unsafe comparison and intentionally
        # ignores provenance/scope; its expected decisions are therefore
        # separate from the conservative policy outputs.
        actual=(r["two_group"],r["contract_singleton"],r["any_singleton"])
        if exp is None or actual!=exp:
            errors.append("decision:"+r["id"])
        if r["expected"] != {"trusted_single_positive":"PASS","trusted_single_negative":"FAIL","independent_two_positive":"PASS","stale_plus_trusted_current":"PASS"}.get(r["id"], "ABSTAIN"):
            errors.append("oracle_label:"+r["id"])
    idx={r["id"]:r for r in rows}
    for policy in ("two_group","contract_singleton","any_singleton"):
        unsafe=[r["id"] for r in rows if r["id"] in {"untrusted_single_positive","missing_provenance","duplicate_same_group","correlated_distinct_labels","stale_only","scope_mismatch_only"} and r[policy]!="ABSTAIN"]
        if policy=="contract_singleton" and unsafe: errors.append("unsafe_upgrade:"+policy+":"+",".join(unsafe))
    # This audit exposes whether the policy's declared exception is actually
    # implemented; current candidate fails because the generic two-group gate
    # runs before the singleton trust contract.
    recovered=(idx.get("trusted_single_positive",{}).get("contract_singleton")=="PASS" and
               idx.get("trusted_single_negative",{}).get("contract_singleton")=="FAIL")
    if idx.get("independent_two_positive",{}).get("contract_singleton")!="PASS": errors.append("independent_coverage_not_admitted")
    if idx.get("stale_plus_trusted_current",{}).get("contract_singleton")!="PASS": errors.append("stale_addition_changed_current_decision")
    if idx.get("trusted_conflict",{}).get("contract_singleton")!="ABSTAIN": errors.append("conflict_not_abstained")
    digest=hashlib.sha256(raw).hexdigest()
    recorded=(d/"raw.sha256").read_text().split()[0]
    if digest!=recorded: errors.append("raw_hash")
    result={"audit":"PASS" if not errors else "FAIL","rows_checked":len(rows),"errors":errors,"raw_sha256":digest,
            "contract_matches_expected":sum(r.get("contract_singleton")==r.get("expected") for r in rows),
            "two_group_matches_expected":sum(r.get("two_group")==r.get("expected") for r in rows),
            "unsafe_any_singleton_cases":sum(r.get("any_singleton")!=r.get("expected") for r in rows),
            "trusted_singleton_recovered":recovered}
    (d/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__=="__main__": main()
