"""Deterministic T0 ledger constructor; it makes no model or human decisions."""
import json
import sys


def feasible_routes(variant):
    return sorted(r["id"] for r in variant["routes"]
                  if r["safe"] is True and r["verified"] is True
                  and r["duration"] <= variant["deadline"]
                  and r["lease_until"] >= r["duration"])


def choose(variant, feasible):
    options=[r for r in variant["routes"] if r["id"] in feasible]
    if not options:
        return "YIELD"
    return sorted(options,key=lambda r:(-r["utility"],r["id"]))[0]["id"]


def context_signature(variant):
    routes=[]
    for r in sorted(variant["routes"],key=lambda x:x["id"]):
        routes.append((r["id"],r["duration"],r["utility"],r["safe"],r["verified"],
                       r["lease_until"]>=r["duration"],r["effect"]))
    return (variant["goal"],variant["intent_version"],variant["observation"],
            variant["guard"],variant["authority"],variant["oracle"],tuple(routes))


def decision_pairs(fixtures):
    output=[]
    for pair in fixtures["decision_pairs"]:
        variants=[]
        for v in pair["variants"]:
            feasible=feasible_routes(v)
            variants.append({"variant":v["id"],"deadline":v["deadline"],
                             "feasible_routes":feasible,"choice":choose(v,feasible)})
        same_context=context_signature(pair["variants"][0])==context_signature(pair["variants"][1])
        if not same_context:
            classification="INVALID_CONTEXT"
        elif variants[0]["feasible_routes"]==variants[1]["feasible_routes"] and variants[0]["choice"]==variants[1]["choice"]:
            classification="SLACK_EQUIVALENT"
        else:
            classification="SLACK_SENSITIVE"
        if pair["claim"]=="SLACK_EQUIVALENT" and classification=="SLACK_EQUIVALENT":
            status="ACCEPTED_EQUIVALENT"
        elif pair["claim"]=="SLACK_SENSITIVE" and classification=="SLACK_SENSITIVE":
            status="ACCEPTED_SLACK_SENSITIVE"
        elif classification=="INVALID_CONTEXT":
            status="REJECTED_CONTEXT_MISMATCH"
        else:
            status="REJECTED_FALSE_EQUIVALENCE"
        output.append({"id":pair["id"],"claim":pair["claim"],"classification":classification,
                       "status":status,"variants":variants})
    return output


def trial_rows(fixtures):
    rows=[]
    for card in fixtures["event_cards"]:
        for budget in fixtures["budgets"]:
            cutoff=float("inf") if budget is None else budget
            delivered=card["delivered_at"]
            proposal=card["proposal_at"]
            effect=card["effect_at"]
            delivered_by=delivered<=cutoff
            proposal_by=proposal is not None and proposal<=cutoff
            effect_by=effect is not None and effect<=cutoff
            rows.append({"card":card["id"],"budget":budget,"clock":"fixture-mono-01",
                         "delivered_at":delivered,"proposal_at":proposal,"effect_at":effect,
                         "proposal_latency":None if proposal is None else proposal-delivered,
                         "effect_after_proposal":None if effect is None or proposal is None else effect-proposal,
                         "delivered_by_deadline":delivered_by,"proposal_by_deadline":proposal_by,
                         "effect_by_deadline":effect_by,
                         "correct_effect_by_deadline":card["outcome"]=="CORRECT" and delivered_by and effect_by,
                         "wrong_effect_by_deadline":card["outcome"]=="WRONG" and delivered_by and effect_by,
                         "forbidden_effect_by_deadline":card["outcome"]=="FORBIDDEN" and delivered_by and effect_by,
                         "abstain_by_deadline":card["outcome"]=="ABSTAIN" and delivered_by and proposal_by,
                         "no_proposal_by_deadline":delivered_by and not proposal_by,
                         "outcome":card["outcome"]})
    return rows


def curves(rows):
    budgets=sorted({r["budget"] for r in rows},key=lambda x:(x is not None,x if x is not None else -1))
    names=("correct_effect_by_deadline","wrong_effect_by_deadline","forbidden_effect_by_deadline",
           "abstain_by_deadline","no_proposal_by_deadline")
    return [{"budget":b,"offered":sum(r["budget"]==b for r in rows),
             **{name:sum(r["budget"]==b and r[name] for r in rows) for name in names}}
            for b in budgets]


def surface_results(fixtures):
    results=[]
    for panel in fixtures["surface_panels"]:
        cells=[]
        for deadline in sorted({x["deadline"] for x in panel["trials"]}):
            for route in sorted({x["route"] for x in panel["trials"]}):
                members=[x for x in panel["trials"] if x["deadline"]==deadline and x["route"]==route]
                correct=sum(x["outcome"]=="CORRECT" and x["effect_at"]<=deadline for x in members)
                cells.append({"deadline":deadline,"route":route,"offered":len(members),"correct_on_time":correct})
        deadlines=sorted({x["deadline"] for x in panel["trials"]})
        diff=[]
        for deadline in deadlines:
            d={x["route"]:x["correct_on_time"]/x["offered"] for x in cells if x["deadline"]==deadline}
            diff.append(d["INTERFACE"]-d["DIRECT"])
        if any(x<0 for x in diff) and any(x>0 for x in diff):
            pattern="RANK_REVERSAL"
        elif all(x==0 for x in diff):
            pattern="NO_INTERACTION_NULL"
        else:
            pattern="NO_RANK_REVERSAL"
        results.append({"id":panel["id"],"cells":cells,"interface_minus_direct":diff,"pattern":pattern})
    return results


def run(path):
    fixtures=json.load(open(path,encoding="utf-8"))
    rows=trial_rows(fixtures)
    return {"schema":"issue6435-t0-output-v1","offered_trial_count":len(rows),
            "trial_rows":rows,"deadline_curves":curves(rows),
            "decision_pairs":decision_pairs(fixtures),"surface_results":surface_results(fixtures)}


if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),sort_keys=True,separators=(",",":")))
