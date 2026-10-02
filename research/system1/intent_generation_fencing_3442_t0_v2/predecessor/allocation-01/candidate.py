import json
TRACE={"stable_no_revision":"stable","revision_before_admission":"revision","admitted_then_revision_before_emit":"cancel","emitted_pending_then_revision":"pending","effect_completed_before_revision":"completed","stale_duplicate_after_revision":"stale","published_but_delivery_uncertain":"undelivered","planner_restart_generation_reuse":"restart","revision_between_check_and_commit":"race","new_intent_forbids_old_action":"forbids","late_effect_receipt_after_revision":"late_receipt"}
POLICIES=("START_ONLY","ADMISSION_FENCE","FENCE_RECONCILE")
def run(case,policy):
 k=TRACE[case]; admit="ADMITTED"; emit=True; status="VERIFIED_EFFECT"; release=False; stale=False
 if k in ("revision","forbids"):
  if policy!="START_ONLY": admit="REFUSED_STALE"; emit=False; status="NO_EFFECT"
  else: status="UNKNOWN_EFFECT_PENDING"
 elif k=="cancel":
  if policy=="FENCE_RECONCILE": emit=False; status="CANCELLED_NO_EMISSION"; release=True
  else: status="UNKNOWN_EFFECT_PENDING"
 elif k=="pending": status="UNKNOWN_EFFECT_PENDING"; release=(policy=="FENCE_RECONCILE")
 elif k=="completed": pass
 elif k=="stale":
  if policy=="START_ONLY": stale=True; status="UNKNOWN_EFFECT_PENDING"
  else: admit="REFUSED_STALE"; emit=False; status="NO_EFFECT"
 elif k=="undelivered":
  if policy=="FENCE_RECONCILE": admit="HOLD_UNDELIVERED_REVISION"; emit=False; status="NO_EFFECT"
  else: status="UNKNOWN_EFFECT_PENDING"
 elif k=="restart":
  if policy=="FENCE_RECONCILE": admit="REFUSED_EPOCH_MISMATCH"; emit=False; status="NO_EFFECT"
  else: status="UNKNOWN_EFFECT_PENDING"
 elif k=="race":
  if policy!="START_ONLY": admit="REFUSED_AT_COMMIT_FENCE"; emit=False; status="NO_EFFECT"
  else: status="UNKNOWN_EFFECT_PENDING"
 elif k=="late_receipt": release=(policy=="FENCE_RECONCILE")
 return {"case":case,"policy":policy,"admission":admit,"emitted":emit,"terminal_effect_status":status,"release_sent":release,"stale_generation_reactivated":stale,"intermediate_unknown_before_receipt":k=="late_receipt"}
for c in TRACE:
 for p in POLICIES: print(json.dumps(run(c,p),sort_keys=True,separators=(",",":")))
