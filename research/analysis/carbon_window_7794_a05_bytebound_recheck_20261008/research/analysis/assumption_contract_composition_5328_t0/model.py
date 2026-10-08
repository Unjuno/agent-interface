"""Toy observer→verifier→broker contract composition."""
CASES={
"baseline":dict(guarantees=(True,True,True),assumptions=("DISCHARGED","DISCHARGED","DISCHARGED"),compatible=True,versions_current=True),
"backend_stability_false":dict(guarantees=(True,True,True),assumptions=("FALSE","DISCHARGED","DISCHARGED"),compatible=True,versions_current=True),
"capability_expired":dict(guarantees=(True,True,True),assumptions=("DISCHARGED","DISCHARGED","FALSE"),compatible=True,versions_current=True),
"protocol_mismatch":dict(guarantees=(True,True,True),assumptions=("DISCHARGED","DISCHARGED","DISCHARGED"),compatible=False,versions_current=True),
"assumption_evidence_missing":dict(guarantees=(True,True,True),assumptions=("UNKNOWN","DISCHARGED","DISCHARGED"),compatible=True,versions_current=True),
"verifier_digest_stale":dict(guarantees=(True,True,True),assumptions=("DISCHARGED","FALSE","DISCHARGED"),compatible=True,versions_current=False),
"component_guarantee_false":dict(guarantees=(True,False,True),assumptions=("DISCHARGED","DISCHARGED","DISCHARGED"),compatible=True,versions_current=True),
}
def evaluate(c):
    local_pass=all(c["guarantees"])
    if not local_pass or not c["compatible"]: composed="STOP"
    elif not c["versions_current"] or any(x!="DISCHARGED" for x in c["assumptions"]): composed="UNKNOWN"
    else: composed="PASS"
    return {"flat_local_pass":local_pass,"composed_status":composed,"authority_minted":False,"external_effect":False}
