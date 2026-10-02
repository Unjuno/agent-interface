import json
TRACES={
"stable_no_revision":{"events":["compile:g0","admit:g0","emit","effect_receipt:verified"],"proposal":["session-A",1],"published":["session-A",1],"delivered":["session-A",1],"pending_delivery":False,"effect_before":"NONE"},
"revision_before_admission":{"events":["compile:g0","publish:g1","deliver_auth:g1","admission_attempt"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"NONE"},
"admitted_then_revision_before_emit":{"events":["compile:g0","admit:g0","publish:g1","deliver_auth:g1","cancel_unemitted","release_verified"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"ADMITTED_UNEMITTED"},
"emitted_pending_then_revision":{"events":["compile:g0","admit:g0","emit","publish:g1","deliver_auth:g1","release_verified","effect_receipt_pending"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"EMITTED_EFFECT_PENDING"},
"effect_completed_before_revision":{"events":["compile:g0","admit:g0","emit","effect_receipt:verified","publish:g1","deliver_auth:g1"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"VERIFIED_EFFECT"},
"stale_duplicate_after_revision":{"events":["deliver_auth:g1","receive_stale:g0","admission_attempt"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"NONE"},
"published_but_delivery_uncertain":{"events":["compile:g0","publish:g1","delivery_pending","admission_attempt"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",1],"pending_delivery":True,"effect_before":"NONE"},
"planner_restart_generation_reuse":{"events":["compile:session-A-g1","restart:session-B-g1","admission_attempt"],"proposal":["session-A",1],"published":["session-B",1],"delivered":["session-B",1],"pending_delivery":False,"effect_before":"NONE"},
"revision_between_check_and_commit":{"events":["compile:g0","precheck:g0","deliver_auth:g1","atomic_commit_check"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"NONE"},
"new_intent_forbids_old_action":{"events":["compile:submit-under-g0","publish:forbid-submit-g1","deliver_auth:g1","admission_attempt"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"NONE"},
"late_effect_receipt_after_revision":{"events":["compile:g0","admit:g0","emit","publish:g1","deliver_auth:g1","release_verified","effect_receipt:late_verified"],"proposal":["session-A",1],"published":["session-A",2],"delivered":["session-A",2],"pending_delivery":False,"effect_before":"EMITTED_EFFECT_PENDING"}}
POLICIES=("START_ONLY","ADMISSION_FENCE","FENCE_RECONCILE")
def decide(name,p):
 t=TRACES[name];kind=name;admit="ADMITTED";emit=True;status="VERIFIED_EFFECT";release=False;stale=False
 if kind in ("revision_before_admission","new_intent_forbids_old_action"):
  if p!="START_ONLY":admit="REFUSED_STALE";emit=False;status="NO_EFFECT"
  else:status="UNKNOWN_EFFECT_PENDING"
 elif kind=="admitted_then_revision_before_emit":
  if p=="FENCE_RECONCILE":emit=False;status="CANCELLED_NO_EMISSION";release=True
  else:status="UNKNOWN_EFFECT_PENDING"
 elif kind=="emitted_pending_then_revision":status="UNKNOWN_EFFECT_PENDING";release=(p=="FENCE_RECONCILE")
 elif kind=="stale_duplicate_after_revision":
  if p=="START_ONLY":stale=True;status="UNKNOWN_EFFECT_PENDING"
  else:admit="REFUSED_STALE";emit=False;status="NO_EFFECT"
 elif kind=="published_but_delivery_uncertain":
  if p=="FENCE_RECONCILE":admit="HOLD_UNDELIVERED_REVISION";emit=False;status="NO_EFFECT"
  else:status="UNKNOWN_EFFECT_PENDING"
 elif kind=="planner_restart_generation_reuse":
  if p=="FENCE_RECONCILE":admit="REFUSED_EPOCH_MISMATCH";emit=False;status="NO_EFFECT"
  else:status="UNKNOWN_EFFECT_PENDING"
 elif kind=="revision_between_check_and_commit":
  if p!="START_ONLY":admit="REFUSED_AT_COMMIT_FENCE";emit=False;status="NO_EFFECT"
  else:status="UNKNOWN_EFFECT_PENDING"
 elif kind=="late_effect_receipt_after_revision":release=(p=="FENCE_RECONCILE")
 return {"case":name,"policy":p,"events":t["events"],"proposal_token":t["proposal"],"published_token":t["published"],"delivered_token":t["delivered"],"pending_delivery":t["pending_delivery"],"effect_before":t["effect_before"],"admission":admit,"emitted":emit,"terminal_effect_status":status,"release_sent":release,"stale_generation_reactivated":stale,"intermediate_unknown_before_receipt":kind=="late_effect_receipt_after_revision"}
for n in TRACES:
 for p in POLICIES:print(json.dumps(decide(n,p),sort_keys=True,separators=(",",":")))
