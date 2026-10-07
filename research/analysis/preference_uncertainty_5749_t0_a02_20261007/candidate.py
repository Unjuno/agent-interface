import json
from pathlib import Path


ROOT=Path(__file__).parent


def step(policy, case):
    support=[x for x in case["support"] if x not in case["forbidden"]]
    if case["reply"] in {"decline","stale"} or not support:
        return "yield",None,0
    if policy=="repeat_open":
        return "open",None,2
    if policy=="fixed_targeted":
        return ("targeted",None,1) if case["locus"]=="known" else ("open",None,2)
    if policy=="offer_candidate":
        return "candidate",support[0],1
    if policy=="evidence_bounded":
        if case["locus"]!="known":
            return "open",None,2
        if case["offer_allowed"] and len(support)==1:
            return "candidate",support[0],1
        if len(support)>1:
            return "open",None,2
        return "targeted",None,1
    raise ValueError("unknown_policy")


def run(fixture):
    rows=[]
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            resolution,candidate,questions=step(policy,case)
            support=[x for x in case["support"] if x not in case["forbidden"]]
            rows.append({"case_id":case["id"],"policy":policy,"resolution":resolution,
                         "candidate":candidate,"questions":questions,
                         "forbidden_effect":candidate in case["forbidden"] if candidate else False,
                         "false_confirmation":bool(candidate and not case["offer_allowed"]),
                         "supported_candidate_count":len(support)})
    return {"schema":"5749-repair-escalation-raw-a02-v1","allocation":fixture["allocation"],"rows":rows}


if __name__=="__main__":
    fixture=json.loads((ROOT/"fixture_a02.json").read_text())
    print(json.dumps(run(fixture),sort_keys=True,separators=(",",":")))
