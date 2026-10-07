import copy
import json
import sys
from pathlib import Path


POLICIES = {"repeat_open", "evidence_bounded", "fixed_targeted", "offer_candidate"}


def audit(doc, fixture):
    errors = []
    cases = {c["id"]: c for c in fixture["cases"]}
    seen = set()
    for row in doc.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in seen or key[0] not in cases or key[1] not in POLICIES:
            errors.append("duplicate_or_unknown_row")
            continue
        seen.add(key)
        c = cases[key[0]]
        reply, policy = c["reply"], key[1]
        support = [x for x in c["support"] if x not in c["forbidden"]]
        if reply in {"decline", "stale"} or not support:
            expected = ("yield", None, 0)
        elif policy == "repeat_open":
            expected = ("open", None, 2)
        elif policy == "fixed_targeted":
            expected = ("targeted", None, 1) if c["locus"] == "known" else ("open", None, 2)
        elif policy == "offer_candidate":
            expected = ("candidate", support[0], 1)
        else:
            expected = (("candidate", support[0], 1) if len(support) == 1 else ("open", None, 2)) if c["locus"] == "known" else ("open", None, 2)
        if (row.get("resolution"), row.get("candidate"), row.get("questions")) != expected:
            errors.append("oracle_mismatch:" + c["id"] + ":" + policy)
        if row.get("forbidden_effect") or (row.get("candidate") and row["candidate"] not in c["support"]):
            errors.append("unsupported_or_forbidden_candidate")
        expected_false = bool(row.get("candidate") and len(support) != 1)
        if row.get("false_confirmation") != expected_false:
            errors.append("false_confirmation_score_mismatch")
    if len(seen) != len(cases) * len(POLICIES):
        errors.append("incomplete_matrix")
    grouped={}
    for r in doc.get("rows",[]):
        x=grouped.setdefault(r["policy"],{"questions":0,"candidate_offers":0,"false_confirmations":0,"yields":0})
        x["questions"] += r["questions"]
        x["candidate_offers"] += int(r["resolution"]=="candidate")
        x["false_confirmations"] += int(r["false_confirmation"])
        x["yields"] += int(r["resolution"]=="yield")
    return {"errors": errors, "rows":len(seen), "by_policy":grouped,"disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def mutations(doc, fixture):
    results=[]
    probes=[
        ("invent_candidate", lambda d: d["rows"][0].update(candidate="Z",resolution="candidate")),
        ("candidate_forbidden", lambda d: d["rows"][6].update(candidate="X",resolution="candidate",forbidden_effect=True)),
        ("decline_as_confirmation", lambda d: next(r for r in d["rows"] if r["case_id"]=="none_unsure_decline" and r["policy"]=="evidence_bounded").update(candidate="A",resolution="candidate")),
        ("stale_reply_reused", lambda d: next(r for r in d["rows"] if r["case_id"]=="stale_choice_version" and r["policy"]=="evidence_bounded").update(candidate="A",resolution="candidate")),
        ("unknown_locus_narrowed", lambda d: next(r for r in d["rows"] if r["case_id"]=="unknown_locus_signal_loss" and r["policy"]=="evidence_bounded").update(resolution="candidate",candidate="A")),
        ("false_confirmation_hidden", lambda d: next(r for r in d["rows"] if r["case_id"]=="multiple_supported_candidates" and r["policy"]=="offer_candidate").update(false_confirmation=False)),
        ("drop_row", lambda d: d["rows"].pop()),
    ]
    for name, mutate in probes:
        mutant=copy.deepcopy(doc); mutate(mutant)
        results.append({"name":name,"rejected":bool(audit(mutant,fixture)["errors"])})
    return results


if __name__ == "__main__":
    doc=json.loads(Path(sys.argv[1]).read_text())
    fixture=json.loads(Path(sys.argv[2]).read_text())
    result=audit(doc,fixture); result["mutations"]=mutations(doc,fixture)
    if not all(x["rejected"] for x in result["mutations"]): result["errors"].append("mutation_escaped")
    result["disposition"]="PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
