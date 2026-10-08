import json,sys
rows=[json.loads(x) for x in sys.stdin if x.strip()]
cases=["stable_no_revision","revision_before_admission","admitted_then_revision_before_emit","emitted_pending_then_revision","effect_completed_before_revision","stale_duplicate_after_revision","published_but_delivery_uncertain","planner_restart_generation_reuse","revision_between_check_and_commit","new_intent_forbids_old_action","late_effect_receipt_after_revision"]
policies=["START_ONLY","ADMISSION_FENCE","FENCE_RECONCILE"];errors=[];expected={(c,p) for c in cases for p in policies};keys=[(r.get("case"),r.get("policy")) for r in rows]
if len(rows)!=33:errors.append("row_count")
if len(set(keys))!=33 or set(keys)!=expected:errors.append("key_set")
by={(r.get("case"),r.get("policy")):r for r in rows}
def ck(c,p,f,v):
 if by.get((c,p),{}).get(f)!=v:errors.append(c+"/"+p+"/"+f)
for p in policies:
 ck("stable_no_revision",p,"admission","ADMITTED");ck("stable_no_revision",p,"emitted",True);ck("stable_no_revision",p,"terminal_effect_status","VERIFIED_EFFECT")
for c in ["revision_before_admission","new_intent_forbids_old_action","stale_duplicate_after_revision"]:
 ck(c,"FENCE_RECONCILE","admission","REFUSED_STALE");ck(c,"FENCE_RECONCILE","emitted",False);ck(c,"FENCE_RECONCILE","stale_generation_reactivated",False)
for p in policies:
 ck("effect_completed_before_revision",p,"terminal_effect_status","VERIFIED_EFFECT")
 ck("emitted_pending_then_revision",p,"terminal_effect_status","UNKNOWN_EFFECT_PENDING")
 ck("late_effect_receipt_after_revision",p,"intermediate_unknown_before_receipt",True)
 ck("late_effect_receipt_after_revision",p,"terminal_effect_status","VERIFIED_EFFECT")
ck("admitted_then_revision_before_emit","FENCE_RECONCILE","emitted",False);ck("admitted_then_revision_before_emit","FENCE_RECONCILE","release_sent",True);ck("admitted_then_revision_before_emit","FENCE_RECONCILE","terminal_effect_status","CANCELLED_NO_EMISSION")
ck("emitted_pending_then_revision","FENCE_RECONCILE","release_sent",True)
ck("published_but_delivery_uncertain","FENCE_RECONCILE","admission","HOLD_UNDELIVERED_REVISION");ck("published_but_delivery_uncertain","FENCE_RECONCILE","emitted",False)
ck("planner_restart_generation_reuse","FENCE_RECONCILE","admission","REFUSED_EPOCH_MISMATCH");ck("planner_restart_generation_reuse","FENCE_RECONCILE","emitted",False)
for p in ["ADMISSION_FENCE","FENCE_RECONCILE"]:
 ck("revision_between_check_and_commit",p,"admission","REFUSED_AT_COMMIT_FENCE");ck("revision_between_check_and_commit",p,"emitted",False)
for r in rows:
 if r.get("case") in ("revision_before_admission","new_intent_forbids_old_action","stale_duplicate_after_revision") and r.get("policy")=="FENCE_RECONCILE" and r.get("admission")=="REFUSED_STALE":
  if r.get("proposal_token")==r.get("delivered_token"):errors.append("false_stale_refusal")
  if not r.get("events"):errors.append("missing_event_trace")
def detects(mut):
 k=[(r.get("case"),r.get("policy")) for r in mut]
 if len(mut)!=33 or len(set(k))!=33 or set(k)!=expected:return True
 b={(r["case"],r["policy"]):r for r in mut}
 tests=[("stable_no_revision","START_ONLY","admission","ADMITTED"),("revision_before_admission","FENCE_RECONCILE","emitted",False),("emitted_pending_then_revision","FENCE_RECONCILE","terminal_effect_status","UNKNOWN_EFFECT_PENDING"),("effect_completed_before_revision","FENCE_RECONCILE","terminal_effect_status","VERIFIED_EFFECT")]
 return any(b.get((c,p),{}).get(f)!=v for c,p,f,v in tests)
mutations=[[r for r in rows if not(r["case"]=="stable_no_revision" and r["policy"]=="START_ONLY")],[dict(r,emitted=True) if r["case"]=="revision_before_admission" and r["policy"]=="FENCE_RECONCILE" else r for r in rows],[dict(r,terminal_effect_status="NO_EFFECT") if r["case"]=="emitted_pending_then_revision" and r["policy"]=="FENCE_RECONCILE" else r for r in rows],[dict(r,terminal_effect_status="NO_EFFECT") if r["case"]=="effect_completed_before_revision" and r["policy"]=="FENCE_RECONCILE" else r for r in rows]]
rejected=sum(detects(m) for m in mutations)
if rejected!=4:errors.append("corruption_controls")
print(json.dumps({"rows":len(rows),"errors":errors,"corruption_controls_rejected":rejected,"corruption_controls_total":4,"method_pass":not errors},sort_keys=True))
sys.exit(0 if not errors else 1)
