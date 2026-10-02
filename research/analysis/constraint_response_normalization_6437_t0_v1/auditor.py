"""Independent audit; does not import candidate code."""
import json
import sys

POLICIES=("SOURCE_ONLY","GENERIC","COUNTEREXAMPLE","CHECKLIST")
ACCEPTED={"ANSWERED","CONFIRMED_FORBIDDEN","CONFIRMED_ALLOWED"}


def expected(case,policy,oracle):
    eligible=[]; invalid=False
    for answer in case["responses"][policy]:
        role_bound=answer["authorized"] and case["respondent_roles"].get(answer["role"]) is True
        current=answer["question_revision"]==case["revision"]
        explicit=answer["status"] in ACCEPTED and answer["meaning"] in ("FORBID","ALLOW_SCOPED")
        privacy_ok=not case["privacy_blocked"]
        if role_bound and current and explicit and privacy_ok:
            eligible.append(answer)
        else:
            invalid=True
    signatures={(a["effect"],a["scope"],a["meaning"]) for a in eligible}
    if len(signatures)>1:
        outcome="CONFLICT"; clauses=[]
    elif signatures:
        effect,scope,meaning=next(iter(signatures))
        clauses=[{"effect":effect,"stance":"FORBID" if meaning=="FORBID" else "ALLOW","scope":scope,
                  "provenance":[{"response_id":a["id"],"policy":policy,"role":a["role"],
                                 "question_revision":a["question_revision"],"task_revision":case["revision"]}
                                for a in eligible]}]
        outcome="APPENDED_"+meaning
    elif invalid:
        outcome="UNKNOWN"; clauses=[]
    else:
        outcome="NOT_ASKED"; clauses=[]
    if oracle[case["id"]][policy]!=outcome:
        outcome="ORACLE_MISMATCH"
    result={"case":case["id"],"policy":policy,"outcome":outcome,
            "source_clauses":case["source_clauses"],"new_clauses":clauses,
            "contract_revision_before":case["revision"],
            "contract_revision_after":case["revision"]+len(clauses)}
    result["append_only"]=result["source_clauses"]==case["source_clauses"] and result["contract_revision_after"]>=result["contract_revision_before"]
    result["authority_granted"]=any(c.get("dispatch_authority",False) or c.get("authority_granted",False) for c in clauses)
    result["private_data_displayed"]=case["private_marker"] in json.dumps(result,sort_keys=True)
    return result


def audit_rows(cases,rows,oracle):
    actual={(r["case"],r["policy"]):r for r in rows}
    expected_rows=[expected(c,p,oracle) for c in cases for p in POLICIES]
    checks=[{"case":e["case"],"policy":e["policy"],"match":actual.get((e["case"],e["policy"]))==e} for e in expected_rows]
    unique=len(actual)==len(rows)==len(cases)*len(POLICIES)
    return {"rows":len(rows),"unique_keys":unique,"rows_match":unique and all(c["match"] for c in checks),"checks":checks,
            "outcome_counts":{name:sum(1 for r in rows if r["outcome"]==name) for name in sorted({r["outcome"] for r in rows})},
            "decision":"PASS_METHOD_SCOPED" if unique and all(c["match"] for c in checks) else "FAIL_METHOD"}


def main(fixture_path,oracle_path,candidate_path):
    fixture=json.load(open(fixture_path,encoding="utf-8"))["cases"]
    oracle=json.load(open(oracle_path,encoding="utf-8"))["expected_outcomes"]
    rows=json.load(open(candidate_path,encoding="utf-8"))
    return audit_rows(fixture,rows,oracle)


if __name__=="__main__":
    print(json.dumps(main(*sys.argv[1:]),sort_keys=True,separators=(",",":")))
