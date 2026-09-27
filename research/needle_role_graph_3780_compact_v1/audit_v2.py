"""Strict post-formal audit of retained compact evidence; no runner import."""
import base64,hashlib,json,sys
e=json.load(open(sys.argv[1],encoding="utf-8"))
raw_bytes=base64.b64decode(e["result_gzip_b64"])
import gzip
payload=gzip.decompress(raw_bytes)
if len(payload)!=e.get("result_bytes"): raise SystemExit("STOP:raw_length")
if hashlib.sha256(payload).hexdigest()!=e.get("result_sha256"): raise SystemExit("STOP:raw_sha256")
r=json.loads(payload); errors=[]; warnings=[]
design=r.get("frozen_design",{})
if design!={"base_rows":512,"support_rows_per_adapter":16,"heldout_rows_per_role":4096,"base_steps":400,"adapter_steps":120,"graph_edges":[["A","B"],["B","C"]],"role_versions":{"A":"base-v1","B":"adapter-B-v1","C":"adapter-C-v1"}}: errors.append("frozen_design")
if r.get("seed")!=3775: errors.append("seed")
if r.get("environment",{}).get("device")!="cpu" or r.get("environment",{}).get("threads")!=1 or r.get("environment",{}).get("deterministic") is not True: errors.append("environment")
if r.get("allocation")!="needle-role-graph-3775-v1": errors.append("unexpected_embedded_allocation")
else: warnings.append("stale_embedded_allocation_label_disclosed")
flat=r.get("flat_dispatch",{}); graph=r.get("graph_dispatch",{})
if set(flat)!={"A","B","C"} or set(graph)!={"A","B","C"}: errors.append("roles")
per_role={}
for role,row in flat.items():
    try: packed=base64.b64decode(row["packed_pairs_b64"],validate=True)
    except Exception: errors.append(role+":packed_decode"); continue
    if len(packed)!=2048: errors.append(role+":packed_length")
    if hashlib.sha256(packed).hexdigest()!=row.get("packed_pairs_sha256"): errors.append(role+":packed_sha")
    nibbles=[c for b in packed for c in (b>>4,b&15)]
    pairs=[((c>>2)&3,c&3) for c in nibbles]
    if row.get("n")!=4096 or len(pairs)!=4096: errors.append(role+":row_count")
    correct=sum(a==b for a,b in pairs)
    if row.get("correct")!=correct or row.get("accuracy")!=correct/4096: errors.append(role+":aggregate")
    g=graph.get(role,{})
    if g.get("packed_pairs_b64")!=row.get("packed_pairs_b64") or g.get("packed_pairs_sha256")!=row.get("packed_pairs_sha256") or g.get("n")!=row.get("n") or g.get("correct")!=row.get("correct"): errors.append(role+":flat_graph_mismatch")
    if correct/4096<0.90: errors.append(role+":threshold")
    per_role[role]={"n":len(pairs),"correct":correct,"accuracy":correct/4096}
controls=r.get("invalid_transition_controls",{})
expected_controls={"unknown_destination","skipped_A_to_C","wrong_source_node","stale_generation","wrong_adapter_version","unverified_outcome","wrong_scope","duplicate_receipt"}
if set(controls)!=expected_controls: errors.append("control_set")
for name in expected_controls-{"duplicate_receipt"}:
    c=controls.get(name,{})
    if c.get("decision")!="YIELD" or c.get("state_unchanged") is not True: errors.append("control:"+name)
dup=controls.get("duplicate_receipt",{})
if dup.get("first_decision")!="ADVANCE" or dup.get("decision")!="YIELD" or dup.get("state_unchanged") is not True: errors.append("duplicate_receipt_sequence")
for key,generation in (("generation_1_valid_transitions",1),("generation_2_valid_transitions",2)):
    log=r.get(key,[])
    expected=[("A","B",f"effect-A-g{generation}"),("B","C",f"effect-B-g{generation}")]
    if [(x.get("from"),x.get("to"),x.get("receipt_id")) for x in log]!=expected: errors.append(key+":sequence")
    if any(x.get("generation")!=generation for x in log): errors.append(key+":generation")
for key in ("generation_1_execution","generation_2_execution"):
    expected_roles=["A","B","C"]; seq=r.get(key,[])
    if [x.get("role") for x in seq]!=expected_roles or any(x.get("decision")!="PROPOSE" for x in seq): errors.append(key+":dispatch_sequence")
    if [x.get("transition") for x in seq[:2]]!=["ADVANCE","ADVANCE"]: errors.append(key+":advance_sequence")
if r.get("generation_1_execution",[{},{}])[0].get("fixed_first_row_effect_verified") is not True or r.get("generation_1_execution",[{},{}])[1].get("fixed_first_row_effect_verified") is not True: errors.append("g1_effect_receipts")
if r.get("generation_2_old_receipt")!={"decision":"YIELD","state_unchanged":True}: errors.append("stale_receipt")
if r.get("generation_2_final_node")!="C": errors.append("g2_final_node")
snap=r.get("adapter_snapshots",{}); exact=r.get("adapter_snapshot_exact",{})
if set(snap)!={"B","C"} or set(exact)!={"B","C"} or not all(exact.values()): errors.append("snapshot_exact")
if any(v.get("bytes",0)<=0 or len(v.get("sha256",""))!=64 for v in snap.values()): errors.append("snapshot_metadata")
if r.get("base_immutable") is not True: errors.append("base_immutable")
out={"disposition":"PASS_AUDIT_V2_CONFIRMED_SCOPED" if not errors else "FAIL_AUDIT_V2","errors":sorted(errors),"warnings":warnings,"raw_sha256":e["result_sha256"],"raw_bytes":len(payload),"heldout_rows":sum(v["n"] for v in per_role.values()),"per_role":per_role}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
