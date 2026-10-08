"""Synthetic exact epoch/authority-bound quiescence receipt gate."""
RETIRED_EPOCH=4
CURRENT_EPOCH=5
RETIRED_AUTHORITY="cap-old"
CURRENT_AUTHORITY="cap-current"
REGISTRY_GENERATION=12
READERS=("r1","r2")
def receipt(reader,epoch=RETIRED_EPOCH,authority=RETIRED_AUTHORITY,generation=REGISTRY_GENERATION,rid=None):
    return {"reader":reader,"epoch":epoch,"authority":authority,"registry_generation":generation,"receipt_id":rid or f"{reader}-e{epoch}"}
def complete(): return [receipt("r1"),receipt("r2")]
CASES={
"valid_complete_bundle":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=complete()),
"receipt_epoch_too_old":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1",3),receipt("r2")]),
"receipt_epoch_too_new":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1",5),receipt("r2")]),
"receipt_epoch_missing":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1",None),receipt("r2")]),
"wrong_retired_authority":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1",authority="cap-other"),receipt("r2")]),
"reader_missing":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1")]),
"registry_changed":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=13,readers=READERS,receipts=complete()),
"duplicate_receipt_identity":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1",rid="dup"),receipt("r2",epoch=3,rid="dup")]),
"valid_new_action_reclaim_blocked":dict(action_epoch=5,action_authority=CURRENT_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=[receipt("r1")]),
"stale_action_valid_reclaim":dict(action_epoch=4,action_authority=RETIRED_AUTHORITY,lease=True,registry_generation=12,readers=READERS,receipts=complete()),
}
def evaluate(c):
    action=(c["action_epoch"]==CURRENT_EPOCH and c["action_authority"]==CURRENT_AUTHORITY and c["lease"])
    ids=[r["receipt_id"] for r in c["receipts"]]
    receipt_valid=(len(ids)==len(set(ids)) and set(r["reader"] for r in c["receipts"])==set(c["readers"]) and len(c["receipts"])==len(c["readers"]) and all(r["epoch"]==RETIRED_EPOCH and r["authority"]==RETIRED_AUTHORITY and r["registry_generation"]==REGISTRY_GENERATION for r in c["receipts"]))
    reclaim=(c["registry_generation"]==REGISTRY_GENERATION and receipt_valid)
    return {"action_admitted":action,"reclaim_allowed":reclaim,"authority_minted":False,"external_effect":False}
