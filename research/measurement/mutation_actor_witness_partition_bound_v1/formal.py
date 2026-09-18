#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, math
from pathlib import Path

ACTORS=("THIS_INTENT","THIS_SESSION_OTHER_INTENT","EXTERNAL_PROCESS","HUMAN","OS")
PARENT_BLOBS={
  "report":"a5ef28df339642cde2d585fcc199197635a1da25",
  "result":"8ff6b368329d05e7724330305ff8cd006401aa42",
  "proof":"9bf2190fab6429b2a98900c20fcf438e7f822efd",
}

def canon(part):
    return tuple(sorted((tuple(sorted(b)) for b in part), key=lambda b:(b[0],len(b),b)))

def partitions(items):
    items=list(items)
    if not items:
        yield tuple(); return
    first=items[0]
    for rest in partitions(items[1:]):
        # New block.
        yield canon(((first,),)+rest)
        # Insert into each existing block.
        for i in range(len(rest)):
            blocks=[list(b) for b in rest]
            blocks[i].append(first)
            yield canon(tuple(tuple(b) for b in blocks))

def all_partitions(n):
    return sorted(set(partitions(tuple(range(n)))), key=lambda p:(len(p),p))

def block_index(part):
    out={}
    for i,b in enumerate(part):
        for x in b: out[x]=i
    return out

def refines(witness,taxonomy):
    t=block_index(taxonomy)
    return all(len({t[x] for x in wb})==1 for wb in witness)

def classifier_feasible(witness,taxonomy):
    # Independent operational test: for each witness value, all hidden actors
    # yielding that value must demand the same taxonomy output label.
    w=block_index(witness); t=block_index(taxonomy)
    by={}
    for a in range(len(ACTORS)):
        by.setdefault(w[a],set()).add(t[a])
    return all(len(labels)==1 for labels in by.values())

def bits_for_states(k):
    return 0 if k<=1 else math.ceil(math.log2(k))

def named(part):
    return [[ACTORS[i] for i in block] for block in part]

def selected(partitions_):
    def P(blocks): return canon(tuple(tuple(ACTORS.index(x) for x in b) for b in blocks))
    exact=P([[a] for a in ACTORS])
    none=P([list(ACTORS)])
    selfbit=P([["THIS_INTENT"],["THIS_SESSION_OTHER_INTENT","EXTERNAL_PROCESS","HUMAN","OS"]])
    session=P([["THIS_INTENT"],["THIS_SESSION_OTHER_INTENT"],["EXTERNAL_PROCESS","HUMAN","OS"]])
    return {"NONE":none,"SELF_BIT":selfbit,"SESSION_SCOPE":session,"EXACT_ACTOR_CLASS":exact}

def run():
    parts=all_partitions(len(ACTORS))
    assert len(parts)==52
    mismatches=[]; feasible=0
    by_witness_cells={}
    for w in parts:
        wc=len(w); by_witness_cells.setdefault(wc,{"witness_partitions":0,"feasible_pairs":0}); by_witness_cells[wc]["witness_partitions"]+=1
        for t in parts:
            r=refines(w,t); f=classifier_feasible(w,t)
            if f: feasible+=1; by_witness_cells[wc]["feasible_pairs"]+=1
            if r!=f: mismatches.append({"witness":named(w),"taxonomy":named(t),"refines":r,"feasible":f})
    sel=selected(parts)
    exact=sel["EXACT_ACTOR_CLASS"]
    selected_out={}
    for name,w in sel.items():
        feasible_tax=[t for t in parts if classifier_feasible(w,t)]
        selected_out[name]={
          "witness_partition":named(w),
          "witness_states":len(w),
          "fixed_length_bits_lower_bound":bits_for_states(len(w)),
          "safe_taxonomy_count":len(feasible_tax),
          "exact_five_class_feasible":classifier_feasible(w,exact),
        }
    exact_min=min(len(w) for w in parts if classifier_feasible(w,exact))
    result={
      "task":"MUTATION-ACTOR-WITNESS-PARTITION-LOWER-BOUND-20260918-001",
      "decision":"PASS_ACTOR_WITNESS_PARTITION_BOUND_SCOPED" if not mismatches and exact_min==5 else "FAIL_LOGIC_INTEGRITY",
      "formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,
      "actors":list(ACTORS),
      "actor_count":len(ACTORS),
      "set_partitions":len(parts),
      "witness_taxonomy_pairs":len(parts)*len(parts),
      "feasible_pairs":feasible,
      "refinement_mismatches":mismatches,
      "selected_rungs":selected_out,
      "exact_five_class_min_witness_states":exact_min,
      "exact_five_class_fixed_length_bits_lower_bound":bits_for_states(exact_min),
      "witness_cell_summary":by_witness_cells,
      "parent_1579_blobs":PARENT_BLOBS,
      "authority_promotions":0,"task_success_promotions":0,
    }
    return result

def validate(result):
    errs=[]
    if result.get("set_partitions")!=52: errs.append("partition_count")
    if result.get("witness_taxonomy_pairs")!=2704: errs.append("pair_count")
    if result.get("refinement_mismatches")!=[]: errs.append("refinement_mismatch")
    if result.get("exact_five_class_min_witness_states")!=5: errs.append("exact_min_states")
    if result.get("exact_five_class_fixed_length_bits_lower_bound")!=3: errs.append("exact_min_bits")
    sr=result.get("selected_rungs",{})
    exp={"NONE":(1,0,1,False),"SELF_BIT":(2,1,2,False),"SESSION_SCOPE":(3,2,5,False),"EXACT_ACTOR_CLASS":(5,3,52,True)}
    for k,v in exp.items():
        x=sr.get(k,{}); got=(x.get("witness_states"),x.get("fixed_length_bits_lower_bound"),x.get("safe_taxonomy_count"),x.get("exact_five_class_feasible"))
        if got!=v: errs.append("selected:"+k+":"+repr(got))
    if result.get("parent_1579_blobs")!=PARENT_BLOBS: errs.append("parent_blobs")
    if result.get("authority_promotions")!=0 or result.get("task_success_promotions")!=0: errs.append("promotion")
    if result.get("formal_invocations")!=1 or result.get("reruns")!=0: errs.append("invocation")
    expected="PASS_ACTOR_WITNESS_PARTITION_BOUND_SCOPED" if not errs else "FAIL_INTEGRITY"
    if result.get("decision")!="PASS_ACTOR_WITNESS_PARTITION_BOUND_SCOPED": errs.append("decision")
    return errs

def corruptions(result):
    out={}
    tests=[]
    q=copy.deepcopy(result); q["set_partitions"]=51; tests.append(("partition_count",q))
    q=copy.deepcopy(result); q["witness_taxonomy_pairs"]=2703; tests.append(("pair_count",q))
    q=copy.deepcopy(result); q["exact_five_class_min_witness_states"]=4; tests.append(("four_state_exact_claim",q))
    q=copy.deepcopy(result); q["exact_five_class_fixed_length_bits_lower_bound"]=2; tests.append(("two_bit_exact_claim",q))
    q=copy.deepcopy(result); q["selected_rungs"]["SELF_BIT"]["exact_five_class_feasible"]=True; tests.append(("self_bit_overclaim",q))
    q=copy.deepcopy(result); q["selected_rungs"]["NONE"]["safe_taxonomy_count"]=2; tests.append(("no_witness_overclaim",q))
    q=copy.deepcopy(result); q["parent_1579_blobs"]["proof"]="0"*40; tests.append(("parent_proof_identity",q))
    for name,q in tests: out[name]=bool(validate(q))
    return out

if __name__=="__main__":
    root=Path(__file__).parent
    r=run(); (root/"RESULT.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    errors=validate(r); controls=corruptions(r)
    audit={"pass":not errors and all(controls.values()),"errors":errors,"corruption_controls":controls,"decision":r["decision"],"result_sha256":hashlib.sha256((root/"RESULT.json").read_bytes()).hexdigest()}
    (root/"AUDIT.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":r["decision"],"partitions":r["set_partitions"],"pairs":r["witness_taxonomy_pairs"],"feasible_pairs":r["feasible_pairs"],"exact_min_states":r["exact_five_class_min_witness_states"],"bits":r["exact_five_class_fixed_length_bits_lower_bound"],"selected":r["selected_rungs"],"controls":controls,"errors":errors},sort_keys=True))
    raise SystemExit(0 if audit["pass"] else 2)
