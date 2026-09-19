from itertools import product

GATES=("physical_task_effect_endpoint","task_effect_contract","matched_arm","arm_bound_audit","terminal_integrity")

def decide(snapshot):
    missing=[k for k in GATES if snapshot.get(k) is not True]
    return {"decision":"AUTHORIZE" if not missing else "HOLD","missing":missing,"authority":False}

def oracle(snapshot):
    ok=all(snapshot.get(k) is True for k in GATES)
    missing=[k for k in GATES if snapshot.get(k) is not True]
    return {"decision":"AUTHORIZE" if ok else "HOLD","missing":missing,"authority":False}

def run():
    current={"physical_task_effect_endpoint":False,"task_effect_contract":True,
              "matched_arm":True,"arm_bound_audit":True,"terminal_integrity":True}
    assert decide(current)==oracle(current)
    assert decide(current)["decision"]=="HOLD"
    authorized=0
    for bits in product((False,True),repeat=5):
        s=dict(zip(GATES,bits)); c=decide(s); o=oracle(s)
        assert c==o,(s,c,o)
        authorized += c["decision"]=="AUTHORIZE"
    assert authorized==1
    controls=[
      {**current,"task_effect_contract":False},
      {**current,"arm_bound_audit":False},
      {**current,"terminal_integrity":False},
      {**current,"physical_task_effect_endpoint":True,"task_effect_contract":False},
      {**current,"physical_task_effect_endpoint":True,"matched_arm":False},
    ]
    for s in controls: assert decide(s)["decision"]=="HOLD"
    print("PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED vectors=32 authorize=1 current=HOLD controls=5/5")
if __name__=="__main__": run()
