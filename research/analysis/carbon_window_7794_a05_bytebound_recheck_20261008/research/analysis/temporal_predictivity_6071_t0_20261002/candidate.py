#!/usr/bin/env python3
"""Frozen schedule-coherence candidate; standard library only."""
import json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

FORBIDDEN = {"arm_content_ref", "arm_effect_truth", "arm_authority", "arm_deadline", "arm_result"}


def entropy(values):
    counts = Counter(values)
    n = len(values)
    return -sum((c/n)*math.log2(c/n) for c in counts.values())


def mutual_information(rows, value):
    joint = Counter((r["type"], value(r)) for r in rows)
    n = len(rows)
    ht = entropy([r["type"] for r in rows])
    hd = entropy([value(r) for r in rows])
    htd = -sum((c/n)*math.log2(c/n) for c in joint.values())
    return ht + hd - htd


def evaluate(data):
    tasks = data["tasks"]
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)) or len(tasks) != data["required"]["task_count"]:
        raise ValueError("task_identity_or_count")
    if any(FORBIDDEN.intersection(t) or set(t)!={"id","type","content_ref","effect_truth","A_ms","B_ms","C_ms"} for t in tasks):
        raise ValueError("arm_specific_semantic_override")
    types = Counter(t["type"] for t in tasks)
    if dict(types) != data["required"]["response_type_counts"]:
        raise ValueError("response_type_counts")
    if any(not t.get("content_ref") or not t.get("effect_truth") for t in tasks):
        raise ValueError("missing_content_or_effect_truth")
    summaries = {}
    for arm in ("A", "B", "C"):
        delays = [t[f"{arm}_ms"] for t in tasks]
        summaries[arm] = {"mean_ms":sum(delays)/len(delays),
                          "variance_ms2":sum((x-sum(delays)/len(delays))**2 for x in delays)/len(delays),
                          "delay_multiset":dict(Counter(delays)),
                          "type_delay_counts":{kind:dict(Counter(t[f"{arm}_ms"] for t in tasks if t["type"]==kind))
                                               for kind in sorted(types)}}
    b,c = summaries["B"],summaries["C"]
    expected_multiset = {int(k):v for k,v in data["required"]["B_C_delay_multiset_ms"].items()}
    expected_by_type = {kind:{int(delay):count for delay,count in counts.items()}
                        for kind,counts in data["required"]["B_type_delay_counts"].items()}
    if summaries["A"]["delay_multiset"] != {data["constant_delay_ms"]:len(tasks)}:
        raise ValueError("A_not_constant")
    if any(abs(summary["mean_ms"]-data["constant_delay_ms"])>1e-12 for summary in summaries.values()):
        raise ValueError("arm_mean_mismatch")
    if b["delay_multiset"] != expected_multiset or c["delay_multiset"] != expected_multiset:
        raise ValueError("B_C_marginal_delays")
    if b["type_delay_counts"] != expected_by_type:
        raise ValueError("B_type_independence_balance")
    if any(t[f"C_ms"] != data["required"]["C_mapping"][t["type"]] for t in tasks):
        raise ValueError("C_not_deterministically_predictive")
    mi_b = mutual_information(tasks,lambda t:t["B_ms"])
    mi_c = mutual_information(tasks,lambda t:t["C_ms"])
    if abs(mi_b)>1e-12 or abs(mi_c-1.0)>1e-12:
        raise ValueError("timing_type_information")
    if any(not {"id","type","content_ref","effect_truth","A_ms","B_ms","C_ms"} <= set(t) for t in tasks):
        raise ValueError("incomplete_task_record")
    orders = data["arm_order_counterbalance"]
    if len(orders)!=3 or any(set(o)!={"A","B","C"} for o in orders):
        raise ValueError("invalid_counterbalance")
    if any(Counter(o[i] for o in orders)!={"A":1,"B":1,"C":1} for i in range(3)):
        raise ValueError("unbalanced_counterbalance")
    task_orders=data["task_order_counterbalance"]
    if len(task_orders)!=2 or any(len(o)!=len(tasks) or set(o)!=set(ids) for o in task_orders):
        raise ValueError("invalid_task_order_counterbalance")
    type_by_id={t["id"]:t["type"] for t in tasks}
    if any(Counter(type_by_id[o[i]] for o in task_orders)!={"READY_TO_REVIEW":1,"NEEDS_HUMAN_DECISION":1} for i in range(len(tasks))):
        raise ValueError("task_type_order_imbalance")
    safe = data["safety_contract"]
    if safe != {"deadline":"none in all arms","authority_change":False,"emergency_alert":False,
                "delay_encodes_correctness":False,"live_actions":False}:
        raise ValueError("safety_or_authority_difference")
    ids_by_content = {t["id"]:(t["content_ref"],t["effect_truth"]) for t in tasks}
    return {"task_count":len(tasks),"type_counts":dict(types),"arms":summaries,
            "B_C_multiset_equal":b["delay_multiset"]==c["delay_multiset"],
            "B_mutual_information_bits":mi_b,"C_mutual_information_bits":mi_c,
            "content_effect_rows":ids_by_content,"counterbalance_balanced":True,"task_order_counterbalanced":True,
            "safety_invariants_hold":True,"disposition":"METHOD_PASS_SCOPED"}


def main():
    data=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({"schema":"6071.candidate.v1","summary":evaluate(data)},sort_keys=True))


if __name__=="__main__": main()
