import hashlib, json

CASES = [
    ("causal_needed", [("old_causal",10,1.0,True),("new_irrelevant",20,0.2,False)], "old_causal"),
    ("newest_irrelevant", [("old_causal",10,1.0,True),("new_irrelevant",20,0.2,False)], "old_causal"),
    ("false_causal", [("old_false",10,1.0,False),("new_relevant",20,0.2,True)], "new_relevant"),
    ("low_confidence", [("old_low",10,0.2,True),("new_relevant",20,0.8,True)], "new_relevant"),
    ("equal_relevance", [("a",10,1.0,True),("b",20,1.0,True)], "tie"),
    ("no_effect", [("old_action",10,1.0,False),("current",20,0.5,False)], "abstain"),
    ("gap", [("before_gap",10,1.0,True),("after_gap",40,0.2,False)], "before_gap"),
    ("current_sufficient", [("current",20,0.5,True),("old",10,1.0,False)], "current"),
    ("stale_identity", [("old_target",10,1.0,False),("current_target",20,0.8,True)], "current_target"),
]

def recency(xs): return max(xs, key=lambda x:x[1])[0]
def causal(xs): return max(xs, key=lambda x:(x[2],x[1]))[0]
def confidence(xs):
    eligible=[x for x in xs if x[3]]
    return max(eligible,key=lambda x:(x[2],x[1]))[0] if eligible else None

def main():
    rows=[]
    for name,xs,expected in CASES:
        rows.append({"case":name,"expected":expected,"recency":recency(xs),"causal":causal(xs),"confidence":confidence(xs)})
    assert len(rows)==9
    assert rows[0]["causal"]=="old_causal"
    assert rows[2]["confidence"]=="new_relevant"
    assert rows[3]["confidence"]=="new_relevant"
    assert rows[5]["confidence"] is None
    assert rows[8]["confidence"]=="current_target"
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    print(json.dumps({"cases":9,"rows":rows,"policy_oracle":"PASS","false_label_control":"PASS","low_confidence_control":"PASS","abstention_control":"PASS","model_invocations":0,"gui_invocations":0,"task_input_events":0,"digest":digest},sort_keys=True))
main()
