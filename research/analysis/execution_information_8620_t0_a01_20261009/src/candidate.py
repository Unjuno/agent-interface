#!/usr/bin/env python3
"""Candidate EIR-aware retain/reacquire policy for frozen finite fixture."""
import itertools, json, pathlib, sys

src=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); data=json.loads(src.read_text())
hist=data["histories"]; fields=list(data["field_cost_bits"])
result={"fixture_id":data["fixture_id"],"policies":{},"contracts":{}}
for name, retained in [("FULL_HISTORY",fields),("FIXED_WINDOW",data["policy_definitions"]["FIXED_WINDOW"]),("TASK_SUMMARY",data["policy_definitions"]["TASK_SUMMARY"])]:
    result["policies"][name]={"retained_fields":retained}
for contract in data["contracts"]:
    schedules=contract["schedules"]; proof=set(contract["proof_fields"])
    needed=set(proof)
    for s in schedules: needed.update(s["reads"])
    # A field is mandatory in storage if it is proof-bearing or cannot be reacquired.
    mandatory={f for f in needed if f in proof or not data["reacquisition"].get(f,{}).get("available",False)}
    # Enumerate every field subset; admissible subsets retain all mandatory fields.
    # Choose minimum storage; ties prefer fewer expected reads, then lexical field order.
    choices=[]
    for n in range(len(fields)+1):
      for combo in itertools.combinations(fields,n):
        retained=set(combo)
        if not mandatory <= retained: continue
        retrieval=sum(s["weight"]*sum(data["reacquisition"][f]["cost_units"] for f in s["reads"] if f not in retained) for s in schedules)
        storage=len(hist)*sum(data["field_cost_bits"][f] for f in retained)
        choices.append((storage+retrieval,storage,retrieval,tuple(f for f in fields if f in retained)))
    _,storage,retrieval,selected=min(choices)
    # Equivalence at the cut preserves all non-reacquirable future distinctions and proof fields.
    key_fields=sorted(mandatory)
    signatures={h["id"]:tuple(h[f] for f in key_fields) for h in hist}
    partition={}
    for hid,sig in signatures.items(): partition.setdefault(json.dumps(sig),[]).append(hid)
    classes=sorted([sorted(v) for v in partition.values()])
    policies={k:v.copy() for k,v in result["policies"].items()}
    policies["EIR_AWARE_RETAIN_OR_REACQUIRE"]={"retained_fields":list(selected)}
    scores={}
    for pname,p in policies.items():
      keep=set(p["retained_fields"]); st=len(hist)*sum(data["field_cost_bits"][f] for f in keep); rec=0; errors=[]
      for s in schedules:
        for f in s["reads"]:
          if f in keep: continue
          if data["reacquisition"].get(f,{}).get("available",False): rec += s["weight"]*data["reacquisition"][f]["cost_units"]
          else: errors.append({"schedule":s["id"],"field":f})
      for f in proof:
        if f not in keep: errors.append({"schedule":"proof","field":f})
      scores[pname]={"storage_bits":st,"expected_reacquisition_units":rec,"unavailable_requirements":errors,"error_count":len(errors)}
    result["contracts"][contract["id"]]={"required_fields":sorted(needed),"mandatory_retained_fields":key_fields,"eir_retained_fields":list(selected),"equivalence_classes":classes,"minimum_storage_bits":storage,"expected_reacquisition_units":retrieval,"policy_scores":scores}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
