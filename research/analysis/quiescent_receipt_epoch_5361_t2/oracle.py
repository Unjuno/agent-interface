"""Independent literal oracle for the one-factor receipt corpus."""
EXPECTED={
"valid_complete_bundle":(True,True),
"receipt_epoch_too_old":(True,False),
"receipt_epoch_too_new":(True,False),
"receipt_epoch_missing":(True,False),
"wrong_retired_authority":(True,False),
"reader_missing":(True,False),
"registry_changed":(True,False),
"duplicate_receipt_identity":(True,False),
"valid_new_action_reclaim_blocked":(True,False),
"stale_action_valid_reclaim":(False,True),
}
