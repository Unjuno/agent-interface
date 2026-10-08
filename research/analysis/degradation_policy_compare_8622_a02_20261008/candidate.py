"""Pure three-arm degradation contract evaluator."""
def _support(spec, case, available):
    evidence=case["evidence"]
    return [{"operation":op["id"],"source":op["source"],"claim":op["claim"],"freshness":"CURRENT"}
            for op in spec["operations"]
            if all(available.get(x,False) for x in op["requires"])
            and all(evidence.get(x) is True for x in op["evidence"])]
def evaluate(spec):
    cases=[]
    for case in spec["scenarios"]:
        lost=set(case["failed_dependencies"])|set(case["corrupted_dependencies"])
        unknown=set(case["unknown_services"])
        dep={s:s not in unknown and not bool(set(ds)&lost) for s,ds in spec["components"].items()}
        indep={s:s not in set(case["naive_unavailable_services"]) for s in spec["components"]}
        closed=({s:False for s in spec["components"]} if unknown else dep)
        cases.append({"case_id":case["id"],"arms":{
            "independence_assuming_lookup":_support(spec,case,indep),
            "dependency_aware_contract":_support(spec,case,dep),
            "unknown_dependency_fail_closed":_support(spec,case,closed)},
            "release_obligation":"MANDATORY_RELEASE"})
    return {"schema":"8622-candidate-v1","cases":cases}
