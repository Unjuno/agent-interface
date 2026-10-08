"""Independent literal raw-only audit. This module does not import breaker.py."""
import base64,json,sys

EXPECTED={
"current_verified_probe_closes":("valid_recovery",{"state":"CLOSED","completion":"CIRCUIT_CLOSED","accepted_probes":["p5"],"denied_probes":[],"fallback":"NONE","authority":False}),
"open_timeout_fallback_unknown":("transient_timeout",{"state":"OPEN","completion":"NO_PROBE_RESULT","accepted_probes":[],"denied_probes":[],"fallback":"DEPENDENCY_UNAVAILABLE","authority":False}),
"semantic_contradiction_mislabeled_transient":("failure_misclassification",{"state":"OPEN","completion":"REOPENED_BAD_EVIDENCE","accepted_probes":[],"denied_probes":[],"fallback":"UNKNOWN","authority":False}),
"late_previous_generation_pass":("half_open_race",{"state":"HALF_OPEN","completion":"IGNORED_STALE_COMPLETION","accepted_probes":[],"denied_probes":[],"fallback":"UNKNOWN","authority":False}),
"single_probe_under_concurrency":("half_open_race",{"state":"CLOSED","completion":"CIRCUIT_CLOSED","accepted_probes":["p9-a"],"denied_probes":["p9-b"],"fallback":"NONE","authority":False}),
"containment_fallback_is_not_authority":("fallback_boundary",{"state":"OPEN","completion":"NO_PROBE_RESULT","accepted_probes":[],"denied_probes":[],"fallback":"CONTAINMENT","authority":False}),
"unknown_authority_fallback_rejected":("fallback_boundary",{"state":"OPEN","completion":"NO_PROBE_RESULT","accepted_probes":[],"denied_probes":[],"fallback":"UNKNOWN","authority":False}),
"stale_evidence_cannot_close":("evidence_currentness",{"state":"OPEN","completion":"REOPENED_BAD_EVIDENCE","accepted_probes":[],"denied_probes":[],"fallback":"UNKNOWN","authority":False}),
"expired_probe_cannot_close":("deadline_race",{"state":"OPEN","completion":"REOPENED_BAD_EVIDENCE","accepted_probes":[],"denied_probes":[],"fallback":"UNKNOWN","authority":False}),
}
BREAKER_SHA="f58c822487a65b37a7832278c5eb1e39a64ffd39"
CORPUS_SHA="db1ed31c93ebb92521a0a5d7c48d5f0012dc9747"

def audit(raw):
    errors=[]
    if raw.get("schema")!="circuit-breaker-5375-boundary-raw-v1": errors.append("schema")
    if raw.get("allocation")!="circuit-breaker-5375-half-open-boundary-20260930-01": errors.append("allocation")
    ident=raw.get("source_identity",{})
    if ident.get("breaker_git_blob_sha")!=BREAKER_SHA: errors.append("breaker_source")
    if ident.get("corpus_git_blob_sha")!=CORPUS_SHA: errors.append("corpus_source")
    rows=raw.get("rows",[])
    ids=[row.get("case_id") for row in rows]
    if ids!=list(EXPECTED): errors.append("case_denominator_or_order")
    for row in rows:
        case_id=row.get("case_id")
        if case_id not in EXPECTED: continue
        family,expected=EXPECTED[case_id]
        if row.get("family")!=family: errors.append(case_id+":family")
        if row.get("expected")!=expected: errors.append(case_id+":embedded_oracle")
        if row.get("predicted")!=expected: errors.append(case_id+":prediction")
        if row.get("match") is not True: errors.append(case_id+":match_flag")
    expected_counts={"cases":9,"exact_matches":9,"mismatches":0,"accepted_probe_permits":2,
                     "denied_probe_requests":1,"authority_outcomes":0}
    if raw.get("counts")!=expected_counts: errors.append("counts")
    if raw.get("side_effects")!={"dispatches":0,"model_calls":0,"gpu_calls":0,"network_calls":0,"authority_grants":0}: errors.append("side_effects")
    if raw.get("disposition")!="PASS_CIRCUIT_BOUNDARY_SCOPED": errors.append("disposition")
    result={"schema":"circuit-breaker-5375-audit-v1","errors":errors,"integrity_pass":not errors,
            "literal_cases_checked":len(EXPECTED),"candidate_imported":False,
            "scope":"raw consistency against independent literal transition table"}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0 if not errors else 1

if __name__=="__main__":
    raw=json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
    raise SystemExit(audit(raw))
