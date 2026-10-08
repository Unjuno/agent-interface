CASES={
"inflight_old_completion":dict(action_epoch=1,action_authority="cap-A",current_epoch=2,current_authority="cap-B",lease=True,revoked=True,started_before_revoke=True,readers=("r1",),receipt_readers=("r1",),receipt_authority="cap-A",registry=7,receipt_registry=7),
"fresh_new_epoch":dict(action_epoch=2,action_authority="cap-B",current_epoch=2,current_authority="cap-B",lease=True,revoked=False,started_before_revoke=False,readers=("r1","r2"),receipt_readers=("r1","r2"),receipt_authority="cap-A",registry=7,receipt_registry=7),
"stale_replay":dict(action_epoch=1,action_authority="cap-A",current_epoch=2,current_authority="cap-B",lease=True,revoked=True,started_before_revoke=False,readers=("r1",),receipt_readers=("r1",),receipt_authority="cap-A",registry=7,receipt_registry=7),
"wrong_authority_same_epoch":dict(action_epoch=2,action_authority="cap-X",current_epoch=2,current_authority="cap-B",lease=True,revoked=False,started_before_revoke=False,readers=("r1",),receipt_readers=("r1",),receipt_authority="cap-A",registry=7,receipt_registry=7),
"expired_lease":dict(action_epoch=2,action_authority="cap-B",current_epoch=2,current_authority="cap-B",lease=False,revoked=False,started_before_revoke=False,readers=("r1",),receipt_readers=("r1",),receipt_authority="cap-A",registry=7,receipt_registry=7),
"crashed_reader_unreported":dict(action_epoch=2,action_authority="cap-B",current_epoch=2,current_authority="cap-B",lease=True,revoked=False,started_before_revoke=False,readers=("r1","r2"),receipt_readers=("r1",),receipt_authority="cap-A",registry=7,receipt_registry=7),
"wrong_retired_authority_receipt":dict(action_epoch=2,action_authority="cap-B",current_epoch=2,current_authority="cap-B",lease=True,revoked=False,started_before_revoke=False,readers=("r1",),receipt_readers=("r1",),receipt_authority="cap-X",registry=7,receipt_registry=7),
"reader_registered_after_snapshot":dict(action_epoch=2,action_authority="cap-B",current_epoch=2,current_authority="cap-B",lease=True,revoked=False,started_before_revoke=False,readers=("r1","r2"),receipt_readers=("r1",),receipt_authority="cap-A",registry=8,receipt_registry=7)}
POLICIES=("REVOKE_ONLY","EPOCH_BOUND")
def evaluate(c,p):
    if p=="REVOKE_ONLY": return {"action_admitted":not c["revoked"] or c["started_before_revoke"],"reclaim_allowed":True}
    ok=c["action_epoch"]==c["current_epoch"] and c["action_authority"]==c["current_authority"] and c["lease"] and not c["revoked"]
    reclaim=set(c["readers"])==set(c["receipt_readers"]) and c["receipt_authority"]=="cap-A" and c["registry"]==c["receipt_registry"]
    return {"action_admitted":ok,"reclaim_allowed":reclaim}
