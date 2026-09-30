"""Small frozen case builder; every IR is validated by the imported #5268 validator."""


def make_case(case_id, check_specs, assignment_specs, status, reasons):
    checks=[]
    assignments=[]
    for spec, assignment in zip(check_specs, assignment_specs):
        check_id, primitive, role, verifier, deadline, dependencies = spec
        checks.append({"check_id":check_id,"primitive":primitive,"subject_ref":f"subject:{check_id}",
                       "criticality":"MANDATORY","required_evidence_role":role,
                       "verifier_class":verifier,"dependencies":dependencies,"deadline":deadline,
                       "budget_class":"bounded","fallback":"YIELD_NO_INPUT"})
        assignments.append({"check_id":check_id,"version":assignment[0],"mode":assignment[1],
                            "budget_ms":assignment[2],"output_evidence_role":assignment[3],
                            "side_effects_allowed":assignment[4]})
    ir={"schema":"verification_ir.v0.1","unknown_check_required":False,"checks":checks}
    normalized=[]
    for value in reasons:
        check_id,reason=value.split(":",1) if ":" in value else (checks[0]["check_id"],value)
        normalized.append({"check_id":check_id,"reason":reason})
    return {"case_id":case_id,"ir":ir,"assignments":assignments,
            "expected_status":status,"expected_reasons":normalized}


CASES=[
    make_case("warm_cpu_feasible",[("c1","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",30,[])],[("2.1.0","warm",20,"CURRENT_OBSERVATION",False)],"COMPATIBLE",[]),
    make_case("unsupported_primitive",[("c2","EFFECT.POSTCONDITION","VERIFIED_EFFECT","local_cpu",30,[])],[("2.1.0","warm",20,"CURRENT_OBSERVATION",False)],"REJECTED",["unsupported_primitive","wrong_evidence_role"]),
    make_case("wrong_input_role",[("c3","TARGET.IDENTITY_CURRENT","CURRENT_PERMISSION","local_cpu",30,[])],[("2.1.0","warm",20,"CURRENT_OBSERVATION",False)],"REJECTED",["wrong_evidence_role"]),
    make_case("wrong_output_role",[("c4","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",30,[])],[("2.1.0","warm",20,"VERIFIED_EFFECT",False)],"REJECTED",["wrong_output_role"]),
    make_case("stale_version",[("c5","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",30,[])],[("2.0.0","warm",20,"CURRENT_OBSERVATION",False)],"REJECTED",["stale_version"]),
    make_case("unknown_verifier",[("c6","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","missing_verifier",30,[])],[("1.0.0","warm",20,"CURRENT_OBSERVATION",False)],"UNAVAILABLE",["verifier_unknown"]),
    make_case("resource_unavailable",[("c7","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_multimodal",500,[])],[("0.1.0-placeholder","warm",500,"CURRENT_OBSERVATION",False)],"UNAVAILABLE",["resource_unavailable","latency_unqualified"]),
    make_case("cold_budget_violation",[("c8","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",100,[])],[("2.1.0","cold",50,"CURRENT_OBSERVATION",False)],"REJECTED",["budget_exceeded"]),
    make_case("hard_incompatibility_precedes_unavailable",[("c9","AUTHORITY.PERMISSION_CURRENT","CURRENT_PERMISSION","external_tool",2000,[])],[("0.9.0-old","warm",2000,"CURRENT_PERMISSION",False)],"REJECTED",["stale_version","side_effect_prohibited","resource_unavailable","latency_unqualified"]),
    make_case("deadline_infeasible",[("c10","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",5,[])],[("2.1.0","warm",20,"CURRENT_OBSERVATION",False)],"REJECTED",["deadline_infeasible"]),
    make_case("full_plan_has_unavailable_member",[("c11","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_multimodal",500,[]),("c12","TARGET.IDENTITY_CURRENT","CURRENT_OBSERVATION","local_cpu",30,["c11"])],[("0.1.0-placeholder","warm",500,"CURRENT_OBSERVATION",False),("2.1.0","warm",20,"CURRENT_OBSERVATION",False)],"UNAVAILABLE",["c11:resource_unavailable","c11:latency_unqualified"]),
]

RESOURCES={"cpu":True,"gpu":False,"network":False}
