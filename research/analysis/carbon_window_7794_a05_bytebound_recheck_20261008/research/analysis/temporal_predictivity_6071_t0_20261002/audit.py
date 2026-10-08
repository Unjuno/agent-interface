#!/usr/bin/env python3
"""Independent reconstruction of frozen timing schedules; no candidate import."""
import json, math, sys
from collections import Counter
from pathlib import Path


def h(items):
    counts=Counter(items); n=len(items)
    return -sum((v/n)*math.log2(v/n) for v in counts.values())


def audit(d):
    rows=d["tasks"]
    if len({r["id"] for r in rows})!=16: raise ValueError("task-count-or-duplicate")
    wanted={"READY_TO_REVIEW":8,"NEEDS_HUMAN_DECISION":8}
    types=Counter(r["type"] for r in rows)
    if dict(types)!=wanted: raise ValueError("type-count")
    schema={"id","type","content_ref","effect_truth","A_ms","B_ms","C_ms"}
    if any(set(r)!=schema for r in rows): raise ValueError("per-arm-content-effect-or-schema-mutation")
    if len({r["id"] for r in rows})!=len({r["content_ref"] for r in rows}): raise ValueError("content-binding")
    results={}
    for arm in "ABC":
        vals=[r[arm+"_ms"] for r in rows]
        avg=sum(vals)/len(vals)
        results[arm]={"mean_ms":avg,"variance_ms2":sum((v-avg)**2 for v in vals)/len(vals),
                      "delay_multiset":dict(Counter(vals)),
                      "type_delay_counts":{kind:dict(Counter(r[arm+"_ms"] for r in rows if r["type"]==kind)) for kind in sorted(wanted)}}
    counts_b={k:dict(Counter(r["B_ms"] for r in rows if r["type"]==k)) for k in sorted(wanted)}
    if counts_b!={k:{2000:4,8000:4} for k in sorted(wanted)}: raise ValueError("B-leaks-response-type")
    if results["B"]["delay_multiset"]!={2000:8,8000:8} or results["C"]["delay_multiset"]!={2000:8,8000:8}: raise ValueError("delay-mass")
    if any(r["C_ms"]!={"READY_TO_REVIEW":2000,"NEEDS_HUMAN_DECISION":8000}[r["type"]] for r in rows): raise ValueError("C-not-predictive")
    mi_b=h([r["type"] for r in rows])+h([r["B_ms"] for r in rows])-h([(r["type"],r["B_ms"]) for r in rows])
    mi_c=h([r["type"] for r in rows])+h([r["C_ms"] for r in rows])-h([(r["type"],r["C_ms"]) for r in rows])
    if abs(mi_b)>1e-12 or abs(mi_c-1)>1e-12: raise ValueError("mutual-information")
    if results["A"]["delay_multiset"]!={5000:16}: raise ValueError("constant-arm")
    if any(abs(results[k]["mean_ms"]-5000)>1e-12 for k in "ABC"): raise ValueError("arm-mean")
    orders=d["arm_order_counterbalance"]
    if len(orders)!=3 or any(sorted(x)!=["A","B","C"] for x in orders): raise ValueError("order-rows")
    if any(Counter(x[i] for x in orders)!=Counter("ABC") for i in range(3)): raise ValueError("order-balance")
    task_orders=d["task_order_counterbalance"]
    task_types={r["id"]:r["type"] for r in rows}
    if len(task_orders)!=2 or any(len(x)!=16 or set(x)!=set(task_types) for x in task_orders): raise ValueError("task-order-coverage")
    if any(Counter(task_types[x[i]] for x in task_orders)!={"READY_TO_REVIEW":1,"NEEDS_HUMAN_DECISION":1} for i in range(16)): raise ValueError("task-order-type-balance")
    if d["safety_contract"]!={"deadline":"none in all arms","authority_change":False,"emergency_alert":False,"delay_encodes_correctness":False,"live_actions":False}: raise ValueError("safety-contract")
    return {"task_count":len(rows),"type_counts":dict(types),"arms":results,
            "B_C_multiset_equal":results["B"]["delay_multiset"]==results["C"]["delay_multiset"],
            "B_type_delay_counts":counts_b,"B_mutual_information_bits":mi_b,"C_mutual_information_bits":mi_c,
            "content_effect_rows":{r["id"]:(r["content_ref"],r["effect_truth"]) for r in rows},
            "counterbalance_balanced":True,"task_order_counterbalanced":True,"safety_invariants_hold":True,"disposition":"METHOD_PASS_SCOPED"}


def main():
    d=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({"schema":"6071.independent-audit.v1","summary":audit(d)},sort_keys=True))


if __name__=="__main__": main()
