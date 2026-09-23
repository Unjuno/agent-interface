from candidate import classify_lineage_bound
from generator import exact_self, external, base_record

controls=[]
r=exact_self(500,50); r["witnesses"][0]["target_id"]+="x"; controls.append(r)
r=exact_self(501,50); r["witnesses"][0]["action_id"]+="x"; controls.append(r)
r=exact_self(502,50); r["witnesses"][0]["intent_id"]+="x"; controls.append(r)
r=exact_self(503,50); r["witnesses"][0]["session_id"]+="x"; controls.append(r)
r=exact_self(504,50); r["witnesses"][0]["delta_kind"]+="x"; controls.append(r)
r=exact_self(505,50); r["witnesses"][0]["time_ms"]=r["action_time_ms"]-1; controls.append(r)
r=exact_self(506,50); r["witnesses"].append({"actor_class":"HUMAN","time_ms":r["mutation_time_ms"],"target_id":r["target_id"],"delta_kind":r["delta_kind"]}); controls.append(r)
r=external(507,"HUMAN",50); controls.append(r)
r=external(508,"OS",50); controls.append(r)
r=external(509,"EXTERNAL_PROCESS",50); controls.append(r)
r=external(510,"THIS_SESSION_OTHER_INTENT",50); controls.append(r)
r=base_record(511,True,50); r["witnesses"]=[{"actor_class":"ALIEN","time_ms":r["mutation_time_ms"]}]; controls.append(r)

safe=sum(classify_lineage_bound(r)["state"]!="SELF_CONFIRMED" for r in controls)
result={"controls":len(controls),"rejected_false_self":safe,"pass":safe==len(controls)}
print(result)
assert result["pass"]
