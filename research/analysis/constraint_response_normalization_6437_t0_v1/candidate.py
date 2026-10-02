import json
import sys

POLICIES=("SOURCE_ONLY","GENERIC","COUNTEREXAMPLE","CHECKLIST")
ACCEPTED={"ANSWERED","CONFIRMED_FORBIDDEN","CONFIRMED_ALLOWED"}


def normalize(case, policy):
    responses=case["responses"][policy]
    eligible=[]
    invalid=False
    for response in responses:
        if (case["privacy_blocked"] or not response["authorized"] or
            not case["respondent_roles"].get(response["role"],False) or
            response["question_revision"]!=case["revision"] or
            response["status"] not in ACCEPTED or
            response["meaning"] not in ("FORBID","ALLOW_SCOPED")):
            invalid=True
            continue
        eligible.append(response)
    meanings={(r["effect"],r["scope"],r["meaning"]) for r in eligible}
    if len(meanings)>1:
        outcome="CONFLICT"; clauses=[]
    elif eligible:
        effect,scope,meaning=next(iter(meanings))
        stance="FORBID" if meaning=="FORBID" else "ALLOW"
        clauses=[{"effect":effect,"stance":stance,"scope":scope,
                  "provenance":[{"response_id":r["id"],"policy":policy,"role":r["role"],
                                 "question_revision":r["question_revision"],"task_revision":case["revision"]}
                                for r in eligible]}]
        outcome="APPENDED_"+meaning
    elif invalid:
        outcome="UNKNOWN"; clauses=[]
    else:
        outcome="NOT_ASKED"; clauses=[]
    return outcome,clauses


def run(path):
    obj=json.load(open(path,encoding="utf-8")); rows=[]
    for case in obj["cases"]:
        for policy in POLICIES:
            outcome,clauses=normalize(case,policy)
            result={"case":case["id"],"policy":policy,"outcome":outcome,
                    "source_clauses":case["source_clauses"],"new_clauses":clauses,
                    "contract_revision_before":case["revision"],
                    "contract_revision_after":case["revision"]+len(clauses)}
            result["append_only"]=result["source_clauses"]==case["source_clauses"] and result["contract_revision_after"]>=result["contract_revision_before"]
            result["authority_granted"]=any(c.get("dispatch_authority",False) or c.get("authority_granted",False) for c in clauses)
            result["private_data_displayed"]=case["private_marker"] in json.dumps(result,sort_keys=True)
            rows.append(result)
    return rows


if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),sort_keys=True,separators=(",",":")))
