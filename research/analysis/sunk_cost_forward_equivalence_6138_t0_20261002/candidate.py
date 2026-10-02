import json,sys
from fractions import Fraction

FORWARD_FIELDS=("present_state","surviving_artifacts","future_success_evidence","remaining_deadline","remaining_budget","safe_actions","options")

def evaluate(card):
    vals={}
    for action in card["safe_actions"]:
        option=card["options"].get(action)
        if option is None or option.get("success_probability") is None or option.get("future_cost") is None or option.get("reward") is None:
            return {"choice":"UNKNOWN","values":{}}
        p=Fraction(option["success_probability"])
        if p<0 or p>1: return {"choice":"UNKNOWN","values":{}}
        vals[action]=str(p*option["reward"]-option["future_cost"])
    if not vals:return {"choice":"UNKNOWN","values":{}}
    best=max(Fraction(x) for x in vals.values()); winners=[a for a,v in vals.items() if Fraction(v)==best]
    choice=winners[0] if len(winners)==1 else "NO_PREFERENCE"
    return {"choice":choice,"values":vals}

def equivalent(a,b):
    return all(a.get(k)==b.get(k) for k in FORWARD_FIELDS)

def run(data):
    cards={c["id"]:c for c in data["cards"]}; results={k:evaluate(c) for k,c in cards.items()}; pairs={}
    for p in data["pairs"]:
        a,b=cards[p["low"]],cards[p["high"]]; eq=equivalent(a,b)
        pairs[p["id"]]={"forward_equivalent":eq,"decision_invariant":(results[a["id"]]["choice"]==results[b["id"]]["choice"]) if eq else None,"accepted_as_matched":eq==p["expect_forward_equivalent"]}
    return {"schema":"sunk-cost-forward-equivalence-result-v1","cards":results,"pairs":pairs}

def main(src,dst):
    data=json.load(open(src,encoding="utf-8")); result=run(data)
    with open(dst,"w",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
if __name__=="__main__":main(*sys.argv[1:3])
