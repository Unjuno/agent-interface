from candidate import classify_lineage_bound, classify_temporal_nearest
from oracle import replay_expected
from generator import exact_self, external, unattributed, base_record

controls=[]
controls.append(exact_self(1,100))
controls.append(exact_self(2,800))
for j,cls in enumerate(["EXTERNAL_PROCESS","HUMAN","OS","THIS_SESSION_OTHER_INTENT"],10): controls.append(external(j,cls,100))
for m in range(6): controls.append(unattributed(20+m,m,100))
r=base_record(40,False,0); r["mutation_time_ms"]=r["action_time_ms"]; controls.append(r)
bad=base_record(41,True,100); bad["target_id"]=""; controls.append(bad)

errs=[]
for idx,r in enumerate(controls):
    a=classify_lineage_bound(r); b=replay_expected(r)
    if a!=b: errs.append({"idx":idx,"candidate":a,"oracle":b})
print({"controls":len(controls),"errors":errs,"temporal_false_examples":sum(classify_temporal_nearest(r)=="SELF_CONFIRMED" and replay_expected(r)["state"]!="SELF_CONFIRMED" for r in controls)})
assert not errs
