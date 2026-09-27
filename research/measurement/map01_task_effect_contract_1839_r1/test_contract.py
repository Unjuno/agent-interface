from contract import classify,oracle
def case(role="good"):
    if role=="good": return [{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":100},{"role":"TASK_EFFECT","plan_id":"p1","actuation_id":"a1","t_ns":200,"effect_id":"e1","scored":True,"scorer_source":"independent"}]
    if role=="state": return [{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":100},{"role":"STATE_FEEDBACK","plan_id":"p1","actuation_id":"a1","t_ns":200,"health_delta":1}]
    if role=="viewport": return [{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":100},{"role":"TASK_EFFECT","plan_id":"p1","actuation_id":"a1","t_ns":200,"effect_id":"v","scored":False,"scorer_source":""}]
    if role=="unbound": return [{"role":"TASK_EFFECT","plan_id":"p9","actuation_id":"a9","t_ns":200,"effect_id":"e","scored":True,"scorer_source":"independent"}]
    if role=="early": return [{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":100},{"role":"TASK_EFFECT","plan_id":"p1","actuation_id":"a1","t_ns":50,"effect_id":"e","scored":True,"scorer_source":"independent"}]
    if role=="terminal": return [{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":100},{"role":"STATE_FEEDBACK","plan_id":"p1","actuation_id":"a1","t_ns":200,"terminal":"completed"}]
def run():
    checks=0
    for name in ("good","state","viewport","unbound","early","terminal"):
        c=classify(case(name)); o=oracle(case(name)); checks+=1
        assert c["task_effect_authority"] is False
        if name=="good": assert c["decision"]=="TASK_EFFECT_BOUND" and o["accepted"]==1
        elif name in ("state","terminal"): assert c["decision"]=="UNRESOLVED_NO_TASK_EFFECT"
        else: assert c["decision"]=="REJECT" and o["accepted"]==0
    dup=case("good")+[dict(case("good")[1],effect_id="e1")]
    assert "duplicate_effect" in classify(dup)["errors"]; checks+=1
    clock=[{"role":"PHYSICAL_ACTUATION","plan_id":"p1","actuation_id":"a1","t_ns":1},{"role":"TASK_EFFECT","plan_id":"p1","actuation_id":"a1","t_ns":2,"effect_id":"e","scored":True,"scorer_source":"independent","clock":"other"}]
    assert classify(clock)["task_effect_authority"] is False; checks+=1
    print(f"PASS_MAP01_TASK_EFFECT_CONTRACT {checks}/8")
if __name__=="__main__": run()
