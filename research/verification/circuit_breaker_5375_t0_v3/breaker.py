"""Generation-bound half-open circuit and non-authoritative typed fallback model."""
SAFE_FALLBACKS=frozenset({"NONE","DEPENDENCY_UNAVAILABLE","UNKNOWN","REOBSERVE","CONTAINMENT","HUMAN_ESCALATION","PRESENTATION_ONLY"})

def simulate(case):
    state=case["state"]
    generation=case["generation"]
    active=case.get("active_probe")
    accepted=[]
    denied=[]
    for token in case.get("probe_requests",[]):
        if state=="HALF_OPEN" and active is None:
            active=token
            accepted.append(token)
        else:
            denied.append(token)
    completion=case.get("completion")
    event="NO_PROBE_RESULT"
    if completion is not None:
        if state!="HALF_OPEN":
            event="IGNORED_NOT_HALF_OPEN"
        elif completion.get("token")!=active or completion.get("generation")!=generation:
            event="IGNORED_STALE_COMPLETION"
        elif (completion.get("evidence")!="VERIFIED_PASS"
              or completion.get("currentness")!="CURRENT"
              or completion.get("contradiction") is not False
              or completion.get("now",float("inf"))>completion.get("deadline",-1)):
            state="OPEN"
            active=None
            event="REOPENED_BAD_EVIDENCE"
        else:
            state="CLOSED"
            active=None
            event="CIRCUIT_CLOSED"
    fallback=case.get("fallback","NONE")
    if fallback not in SAFE_FALLBACKS:
        fallback="UNKNOWN"
    return {"state":state,"completion":event,"accepted_probes":accepted,
            "denied_probes":denied,"fallback":fallback,"authority":False}
