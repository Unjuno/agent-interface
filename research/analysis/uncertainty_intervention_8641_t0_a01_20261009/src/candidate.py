#!/usr/bin/env python3
"""Select observation interventions from public uncertainty summaries only."""
import json
import pathlib
import sys

Q = json.loads(pathlib.Path(sys.argv[1]).read_text())
F = json.loads(pathlib.Path(sys.argv[2]).read_text())

def estimate_source(case):
    cues=case["source_cues"]
    ordered=sorted(cues.items(),key=lambda item:(item[1],item[0]),reverse=True)
    return ordered[0][0],ordered[0][1]-ordered[1][1]

def choose(policy, case):
    if policy == "DECOMPOSED":
        source,confidence=estimate_source(case)
        if confidence < Q["decomposition_confidence_floor"] or case["dependency_warning"]:
            return "UNKNOWN"
        return {"ALEATORIC": "REPEAT", "EPISTEMIC": "ALTERNATE", "DYNAMIC": "WAIT", "INTENT": "UNKNOWN"}[source]
    if policy == "TOTAL_UNCERTAINTY":
        u = case["total_uncertainty"]
        t = Q["total_uncertainty_thresholds"]
        if u >= t["repeat_at_or_above"]: return "REPEAT"
        if u >= t["alternate_at_or_above"]: return "ALTERNATE"
        if u >= t["wait_at_or_above"]: return "WAIT"
        return "UNKNOWN"
    if policy == "DECISION_VALUE":
        if case["decision_value_confidence"] < Q["decision_value_confidence_floor"]: return "UNKNOWN"
        w = Q["decision_value_cost_weight"]
        values = {a: case["estimated_correct_probability"][a] - w * Q["costs"][a] for a in Q["actions"]}
        return max(Q["actions"], key=lambda a: (values[a], -Q["actions"].index(a)))
    if policy == "FIXED_REPEAT": return "REPEAT"
    raise ValueError(policy)

rows=[]
for seed in F["replicate_seeds"]:
    for case in F["cases"]:
        for policy in Q["policies"]:
            action=choose(policy,case)
            rows.append({"seed":seed,"case_id":case["case_id"],"policy":policy,"action":action,"reported_cost":Q["costs"][action],"hard_gates":dict(Q["hard_gates"])})
pathlib.Path(sys.argv[3]).write_text(json.dumps({"protocol_id":Q["protocol_id"],"rows":rows},separators=(",",":"))+"\n")
