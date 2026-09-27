"""Independent compact-row auditor. It does not import the candidate runner."""
import base64, hashlib, json, sys
r=json.load(open(sys.argv[1],encoding="utf-8")); errors=[]; by_role={}
for role,row in r.get("flat_dispatch",{}).items():
    try: packed=base64.b64decode(row["packed_pairs_b64"],validate=True)
    except Exception: errors.append(role+":base64"); continue
    if len(packed)!=2048: errors.append(role+":packed_length")
    digest=hashlib.sha256(packed).hexdigest()
    if digest!=row.get("packed_pairs_sha256"): errors.append(role+":sha")
    codes=[]
    for v in packed: codes.extend((v>>4,v&15))
    pairs=[(c>>2,c&3) for c in codes]
    pairs=pairs[:row.get("n",0)]
    correct=sum(a==b for a,b in pairs)
    if row.get("n")!=4096 or len(pairs)!=4096: errors.append(role+":row_count")
    if correct!=row.get("correct"): errors.append(role+":correct")
    if row.get("accuracy")!=correct/4096: errors.append(role+":accuracy")
    graph=r.get("graph_dispatch",{}).get(role,{})
    if graph.get("packed_pairs_b64")!=row.get("packed_pairs_b64") or graph.get("packed_pairs_sha256")!=digest: errors.append(role+":flat_graph_mismatch")
    by_role[role]={"n":len(pairs),"correct":correct,"accuracy":correct/4096}
if set(by_role)!={"A","B","C"}: errors.append("roles")
for role,x in by_role.items():
    if x["accuracy"]<.90: errors.append(role+":threshold")
for key,generation in (("generation_1_valid_transitions",1),("generation_2_valid_transitions",2)):
    log=r.get(key,[])
    if [(x.get("from"),x.get("to")) for x in log]!=[("A","B"),("B","C")]: errors.append(key+":edges")
    if any(x.get("generation")!=generation for x in log): errors.append(key+":generation")
controls=r.get("invalid_transition_controls",{})
if len(controls)!=8: errors.append("control_count")
for k,v in controls.items():
    if v.get("decision")!="YIELD" or v.get("state_unchanged") is not True: errors.append("control:"+k)
if r.get("generation_2_old_receipt")!={"decision":"YIELD","state_unchanged":True}: errors.append("stale_receipt")
if r.get("generation_2_final_node")!="C": errors.append("g2_final_node")
if not all(r.get("adapter_snapshot_exact",{}).values()) or set(r.get("adapter_snapshot_exact",{}))!={"B","C"}: errors.append("adapter_snapshot")
if r.get("base_immutable") is not True: errors.append("base_immutable")
print(json.dumps({"disposition":"PASS_AUDIT_CONFIRMED_SCOPED" if not errors else "FAIL_AUDIT","errors":errors,"heldout_rows":sum(x["n"] for x in by_role.values()),"per_role":by_role},sort_keys=True,separators=(",",":")))
