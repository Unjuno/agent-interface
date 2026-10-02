"""Independent raw-only reconstruction; deliberately imports no candidate code."""
import json
import sys


def audit(fixture_path, output_path):
    f=json.load(open(fixture_path,encoding="utf-8"))
    got=json.load(open(output_path,encoding="utf-8"))
    expected_rows=[]
    for item in f["event_cards"]:
        for limit in f["budgets"]:
            t=limit if limit is not None else float("inf")
            sent=item["delivered_at"]
            proposed=item["proposal_at"]
            done=item["effect_at"]
            sent_ok=sent<=t
            proposed_ok=proposed is not None and proposed<=t
            done_ok=done is not None and done<=t
            expected_rows.append({"card":item["id"],"budget":limit,"clock":"fixture-mono-01",
                "delivered_at":sent,"proposal_at":proposed,"effect_at":done,
                "proposal_latency":None if proposed is None else proposed-sent,
                "effect_after_proposal":None if proposed is None or done is None else done-proposed,
                "delivered_by_deadline":sent_ok,"proposal_by_deadline":proposed_ok,"effect_by_deadline":done_ok,
                "correct_effect_by_deadline":item["outcome"]=="CORRECT" and sent_ok and done_ok,
                "wrong_effect_by_deadline":item["outcome"]=="WRONG" and sent_ok and done_ok,
                "forbidden_effect_by_deadline":item["outcome"]=="FORBIDDEN" and sent_ok and done_ok,
                "abstain_by_deadline":item["outcome"]=="ABSTAIN" and sent_ok and proposed_ok,
                "no_proposal_by_deadline":sent_ok and not proposed_ok,"outcome":item["outcome"]})

    expected_curves=[]
    limits=list(f["budgets"])
    for limit in limits:
        subset=[r for r in expected_rows if r["budget"]==limit]
        expected_curves.append({"budget":limit,"offered":len(subset),
            "correct_effect_by_deadline":sum(r["correct_effect_by_deadline"] for r in subset),
            "wrong_effect_by_deadline":sum(r["wrong_effect_by_deadline"] for r in subset),
            "forbidden_effect_by_deadline":sum(r["forbidden_effect_by_deadline"] for r in subset),
            "abstain_by_deadline":sum(r["abstain_by_deadline"] for r in subset),
            "no_proposal_by_deadline":sum(r["no_proposal_by_deadline"] for r in subset)})

    expected_pairs=[]
    for pair in f["decision_pairs"]:
        evaluated=[]
        signatures=[]
        for v in pair["variants"]:
            permitted=[]
            signature=[]
            for option in v["routes"]:
                valid_lease=option["lease_until"]>=option["duration"]
                signature.append((option["id"],option["duration"],option["utility"],option["safe"],
                                  option["verified"],valid_lease,option["effect"]))
                if (option["safe"] is True and option["verified"] is True and valid_lease
                    and option["duration"]<=v["deadline"]):
                    permitted.append(option)
            signatures.append((v["goal"],v["intent_version"],v["observation"],v["guard"],
                               v["authority"],v["oracle"],tuple(sorted(signature))))
            if permitted:
                top=sorted(permitted,key=lambda option:(-option["utility"],option["id"]))[0]["id"]
            else:
                top="YIELD"
            evaluated.append({"variant":v["id"],"deadline":v["deadline"],
                              "feasible_routes":sorted(x["id"] for x in permitted),"choice":top})
        contexts_match=signatures[0]==signatures[1]
        if not contexts_match:
            kind="INVALID_CONTEXT"
        elif (evaluated[0]["feasible_routes"]==evaluated[1]["feasible_routes"]
              and evaluated[0]["choice"]==evaluated[1]["choice"]):
            kind="SLACK_EQUIVALENT"
        else:
            kind="SLACK_SENSITIVE"
        if pair["claim"]=="SLACK_EQUIVALENT" and kind=="SLACK_EQUIVALENT":
            status="ACCEPTED_EQUIVALENT"
        elif pair["claim"]=="SLACK_SENSITIVE" and kind=="SLACK_SENSITIVE":
            status="ACCEPTED_SLACK_SENSITIVE"
        elif kind=="INVALID_CONTEXT":
            status="REJECTED_CONTEXT_MISMATCH"
        else:
            status="REJECTED_FALSE_EQUIVALENCE"
        expected_pairs.append({"id":pair["id"],"claim":pair["claim"],"classification":kind,
                               "status":status,"variants":evaluated})

    expected_surfaces=[]
    for panel in f["surface_panels"]:
        cells=[]
        deadlines=sorted(set(x["deadline"] for x in panel["trials"]))
        routes=sorted(set(x["route"] for x in panel["trials"]))
        for limit in deadlines:
            for route in routes:
                subset=[x for x in panel["trials"] if x["deadline"]==limit and x["route"]==route]
                successes=sum(x["outcome"]=="CORRECT" and x["effect_at"]<=limit for x in subset)
                cells.append({"deadline":limit,"route":route,"offered":len(subset),"correct_on_time":successes})
        deltas=[]
        for limit in deadlines:
            rates={c["route"]:c["correct_on_time"]/c["offered"] for c in cells if c["deadline"]==limit}
            deltas.append(rates["INTERFACE"]-rates["DIRECT"])
        if min(deltas)<0<max(deltas):
            shape="RANK_REVERSAL"
        elif all(delta==0 for delta in deltas):
            shape="NO_INTERACTION_NULL"
        else:
            shape="NO_RANK_REVERSAL"
        expected_surfaces.append({"id":panel["id"],"cells":cells,
                                  "interface_minus_direct":deltas,"pattern":shape})

    expected={"schema":"issue6435-t0-output-v1","offered_trial_count":len(expected_rows),
              "trial_rows":expected_rows,"deadline_curves":expected_curves,
              "decision_pairs":expected_pairs,"surface_results":expected_surfaces}
    return {"decision":"METHOD_PASS_SCOPED" if got==expected else "FAIL_METHOD",
            "exact_reconstruction":got==expected,"expected_trial_rows":len(expected_rows),
            "observed_trial_rows":len(got.get("trial_rows",[])),
            "trial_denominators":{str(row["budget"]):row["offered"] for row in expected_curves},
            "decision_statuses":{row["id"]:row["status"] for row in expected_pairs},
            "surface_patterns":{row["id"]:row["pattern"] for row in expected_surfaces}}


if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1],sys.argv[2]),sort_keys=True,separators=(",",":")))
