#!/usr/bin/env python3
"""Independent raw-only reconstruction; intentionally does not import candidate."""
import hashlib, json, sys

def canonical_sha(v):
    b=json.dumps(v,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def reconstruct(case, policy):
    actions=case["plan"].get("actions", [])
    if not actions: return False
    for a in actions:
        if a.get("target") != policy["target"]: return False
        if a.get("epoch") != policy["epoch"]: return False
        if a.get("footprint") != policy["footprint"]: return False
        if a.get("lease_expires_at", -1) < policy["now"]: return False
        if a.get("release_required") is not True: return False
    return True

def main(cases_path, raw_path, out_path):
    data=json.load(open(cases_path)); raw=json.load(open(raw_path)); got={r["id"]:r for r in raw["rows"]}; errors=[]
    if raw.get("allocation") != data["allocation"]: errors.append("allocation mismatch")
    if set(got) != {c["id"] for c in data["cases"]}: errors.append("row key mismatch")
    for c in data["cases"]:
        r=got.get(c["id"])
        if r is None: continue
        expect=reconstruct(c,data["policy"])
        cert=c.get("certificate") or {}
        cert_ok=expect and cert.get("plan_sha256") == canonical_sha(c["plan"]) and set(cert.get("predicates", [])) == set(data["policy"]["required_predicates"])
        # Reconstruct the certificate predicates independently; the positive
        # corpus requires a certificate claim to equal both policy and plan.
        if cert_ok:
            for a in c["plan"].get("actions", []):
                cert_ok &= (cert.get("target") == a.get("target") == data["policy"]["target"])
                cert_ok &= (cert.get("epoch") == a.get("epoch") == data["policy"]["epoch"])
                cert_ok &= (cert.get("footprint") == a.get("footprint") == data["policy"]["footprint"])
                cert_ok &= (cert.get("lease_expires_at") == a.get("lease_expires_at") and data["policy"]["now"] <= cert.get("lease_expires_at", -1) <= data["policy"]["lease_expires_at"])
                cert_ok &= (cert.get("release_required") is True and a.get("release_required") is True)
        expected_full_effect=c["expected_effect"] if expect else "not-dispatched"
        expected_cert_effect=c["expected_effect"] if cert_ok else "not-dispatched"
        if r.get("full",{}).get("admit") != expect: errors.append(f"{c['id']} full admission")
        if r.get("full",{}).get("effect") != expected_full_effect: errors.append(f"{c['id']} full effect")
        if r.get("certificate",{}).get("admit") != cert_ok: errors.append(f"{c['id']} certificate admission")
        if r.get("certificate",{}).get("effect") != expected_cert_effect: errors.append(f"{c['id']} certificate effect")
        expected_full_cost=5*len(c["plan"].get("actions", []))
        cert_prefix=1 if cert.get("plan_sha256") != canonical_sha(c["plan"]) or set(cert.get("predicates", [])) != set(data["policy"]["required_predicates"]) else 0
        expected_cert_cost=cert_prefix or (5*len(c["plan"].get("actions", []))+5+2)
        if r.get("full",{}).get("inspections") != expected_full_cost: errors.append(f"{c['id']} full cost")
        if r.get("certificate",{}).get("inspections") != expected_cert_cost: errors.append(f"{c['id']} certificate cost")
        if r.get("no_certificate",{}).get("admit") is not False: errors.append(f"{c['id']} fail-closed")
    summary={"allocation":data["allocation"],"rows":len(data["cases"]),"errors":errors,"audit":"PASS" if not errors else "FAIL"}
    json.dump(summary,open(out_path,"w"),sort_keys=True,indent=2)
    print(json.dumps(summary,sort_keys=True))
    return 0 if not errors else 2
if __name__=="__main__": raise SystemExit(main(*sys.argv[1:]))
