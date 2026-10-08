import json,sys
from fractions import Fraction

FIELDS=("present_state","surviving_artifacts","future_success_evidence","remaining_deadline","remaining_budget","safe_actions","options")

def oracle(card):
    values={}
    for a in card["safe_actions"]:
        o=card["options"].get(a)
        if not o or o.get("success_probability") is None or o.get("future_cost") is None or o.get("reward") is None:return "UNKNOWN",{}
        p=Fraction(o["success_probability"])
        if p<0 or p>1:return "UNKNOWN",{}
        values[a]=p*o["reward"]-o["future_cost"]
    if not values:return "UNKNOWN",{}
    m=max(values.values()); winners=[a for a,v in values.items() if v==m]
    return (winners[0] if len(winners)==1 else "NO_PREFERENCE"),{a:str(v) for a,v in values.items()}

def audit(data,out):
    errors=[]; cards={c["id"]:c for c in data["cards"]}; got=out.get("cards",{})
    if set(got)!=set(cards):errors.append("card_set")
    for cid,c in cards.items():
        choice,values=oracle(c); actual=got.get(cid,{})
        if actual.get("choice")!=choice or actual.get("values")!=values:errors.append("oracle_mismatch:"+cid)
    pairs=out.get("pairs",{})
    if set(pairs)!={p["id"] for p in data["pairs"]}:errors.append("pair_set")
    for p in data["pairs"]:
        a,b=cards[p["low"]],cards[p["high"]]
        equal=all(a.get(k)==b.get(k) for k in FIELDS)
        row=pairs.get(p["id"],{})
        if equal!=p["expect_forward_equivalent"] or row.get("forward_equivalent")!=equal or row.get("accepted_as_matched") is not True:errors.append("equivalence:"+p["id"])
        if equal and row.get("decision_invariant") is not True:errors.append("invariance:"+p["id"])
        if not equal and row.get("decision_invariant") is not None:errors.append("invalid_pair_claimed_invariant:"+p["id"])
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL","cards_reconstructed":len(cards),"pairs_reconstructed":len(data["pairs"]),"errors":errors}

def main(ip,op,dp):
    data=json.load(open(ip));out=json.load(open(op));result=audit(data,out)
    with open(dp,"w") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(result,sort_keys=True));return 0 if not result["errors"] else 1
if __name__=="__main__":raise SystemExit(main(*sys.argv[1:4]))
