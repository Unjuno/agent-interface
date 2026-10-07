import copy
import json
import sys
from pathlib import Path


POLICIES={"repeat_open","evidence_bounded","fixed_targeted","offer_candidate"}


def oracle(policy,case):
    support=[x for x in case["support"] if x not in case["forbidden"]]
    if case["reply"] in {"decline","stale"} or not support:
        return "yield",None,0
    if policy=="repeat_open": return "open",None,2
    if policy=="fixed_targeted": return (("targeted",None,1) if case["locus"]=="known" else ("open",None,2))
    if policy=="offer_candidate": return "candidate",support[0],1
    if case["locus"]!="known": return "open",None,2
    if case["offer_allowed"] and len(support)==1: return "candidate",support[0],1
    if len(support)>1: return "open",None,2
    return "targeted",None,1


def audit(doc,fixture):
    errors=[]; cases={c["id"]:c for c in fixture["cases"]}; seen=set()
    for row in doc.get("rows",[]):
        key=(row.get("case_id"),row.get("policy"))
        if key in seen or key[0] not in cases or key[1] not in POLICIES:
            errors.append("duplicate_or_unknown_row"); continue
        seen.add(key); case=cases[key[0]]; expected=oracle(key[1],case)
        observed=(row.get("resolution"),row.get("candidate"),row.get("questions"))
        if observed!=expected: errors.append("policy_oracle_mismatch:"+str(key))
        candidate=row.get("candidate")
        false_confirmation=bool(candidate and not case["offer_allowed"])
        if row.get("false_confirmation")!=false_confirmation: errors.append("false_confirmation_mismatch")
        if row.get("forbidden_effect") or (candidate and candidate not in case["support"]): errors.append("unsupported_or_forbidden_effect")
        if row.get("supported_candidate_count")!=len([x for x in case["support"] if x not in case["forbidden"]]): errors.append("support_count_mismatch")
    if len(seen)!=len(cases)*len(POLICIES): errors.append("matrix_incomplete")
    by_policy={}
    for row in doc.get("rows",[]):
        s=by_policy.setdefault(row["policy"],{"questions":0,"narrowed_candidate_resolutions":0,"false_confirmations":0,"yields":0})
        s["questions"]+=row["questions"];s["narrowed_candidate_resolutions"]+=int(row["resolution"]=="candidate")
        s["false_confirmations"]+=int(row["false_confirmation"]);s["yields"]+=int(row["resolution"]=="yield")
    # This method gate tests accounting/contracts and controls, not universal dominance.
    return {"errors":errors,"rows":len(seen),"by_policy":by_policy,
            "disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def mutations(doc,fixture):
    probes=[
      ("invent_candidate",lambda d:d["rows"][0].update(candidate="Z",resolution="candidate")),
      ("candidate_forbidden",lambda d:next(r for r in d["rows"] if r["case_id"]=="candidate_forbidden" and r["policy"]=="offer_candidate").update(forbidden_effect=True)),
      ("decline_as_confirmation",lambda d:next(r for r in d["rows"] if r["case_id"]=="none_unsure_decline" and r["policy"]=="evidence_bounded").update(candidate="A",resolution="candidate")),
      ("stale_reply_reused",lambda d:next(r for r in d["rows"] if r["case_id"]=="stale_choice_version" and r["policy"]=="evidence_bounded").update(candidate="A",resolution="candidate")),
      ("unknown_locus_narrowed",lambda d:next(r for r in d["rows"] if r["case_id"]=="unknown_locus_signal_loss" and r["policy"]=="evidence_bounded").update(candidate="A",resolution="candidate")),
      ("false_confirmation_hidden",lambda d:next(r for r in d["rows"] if r["case_id"]=="multiple_supported_candidates" and r["policy"]=="offer_candidate").update(false_confirmation=False)),
      ("expected_contract_mutated",lambda d:d["rows"][4].update(resolution="candidate")),
      ("drop_row",lambda d:d["rows"].pop())]
    out=[]
    for name,mutate in probes:
        mutant=copy.deepcopy(doc);mutate(mutant);out.append({"name":name,"rejected":bool(audit(mutant,fixture)["errors"])})
    return out


if __name__=="__main__":
    doc=json.loads(Path(sys.argv[1]).read_text());fixture=json.loads(Path(sys.argv[2]).read_text())
    result=audit(doc,fixture);result["mutations"]=mutations(doc,fixture)
    if not all(x["rejected"] for x in result["mutations"]):result["errors"].append("mutation_escaped")
    result["disposition"]="PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result,sort_keys=True));raise SystemExit(0 if not result["errors"] else 1)
