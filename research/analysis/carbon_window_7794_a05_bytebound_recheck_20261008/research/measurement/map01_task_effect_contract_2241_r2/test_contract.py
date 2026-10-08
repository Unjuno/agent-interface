from contract import classify, oracle

def case(name: str):
    physical = {"role": "PHYSICAL_ACTUATION", "plan_id": "p1", "actuation_id": "a1",
                "t_ns": 100, "clock_domain": "monotonic_ns"}
    effect = {"role": "TASK_EFFECT", "plan_id": "p1", "actuation_id": "a1",
              "t_ns": 200, "effect_id": "e1", "scored": True,
              "scorer_source": "independent", "clock_domain": "monotonic_ns"}
    if name == "good": return [physical, effect]
    if name == "state": return [physical, {"role": "STATE_FEEDBACK", "plan_id": "p1", "actuation_id": "a1", "t_ns": 200, "health_delta": 1}]
    if name == "viewport": return [physical, {**effect, "effect_id": "v", "scored": False, "scorer_source": ""}]
    if name == "unbound": return [{**effect, "plan_id": "p9", "actuation_id": "a9", "effect_id": "e"}]
    if name == "early": return [physical, {**effect, "t_ns": 50, "effect_id": "early"}]
    if name == "terminal": return [physical, {"role": "STATE_FEEDBACK", "plan_id": "p1", "actuation_id": "a1", "t_ns": 200, "terminal": "completed"}]
    if name == "clock": return [physical, {**effect, "clock_domain": "other", "effect_id": "clock"}]
    if name == "malformed_timestamp": return [physical, {**effect, "t_ns": "later", "effect_id": "bad-time"}]
    raise ValueError(name)

def run():
    checks = 0
    for name in ("good", "state", "viewport", "unbound", "early", "terminal", "clock", "malformed_timestamp"):
        classified = classify(case(name))
        observed = oracle(case(name))
        assert classified["task_effect_authority"] is False
        if name == "good":
            assert classified["decision"] == "TASK_EFFECT_BOUND" and observed["accepted"] == 1
        elif name in ("state", "terminal"):
            assert classified["decision"] == "UNRESOLVED_NO_TASK_EFFECT"
        else:
            assert classified["decision"] == "REJECT" and observed["accepted"] == 0
        checks += 1
    duplicate = case("good") + [{**case("good")[1], "effect_id": "e1"}]
    assert "duplicate_effect" in classify(duplicate)["errors"]
    print(f"PASS_MAP01_TASK_EFFECT_CONTRACT {checks}/8")

if __name__ == "__main__":
    run()
