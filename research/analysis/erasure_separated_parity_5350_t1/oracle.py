"""Independent literal case expectations."""
EXPECTED={
"complete":("DECODED",True,[],True),
"reordered_complete":("DECODED",True,[],True),
"single_noncritical_erasure":("DECODED",True,["a"],False),
"single_critical_erasure":("DECODED",True,["c"],False),
"cross_group_erasures":("DECODED",True,["a","c"],False),
"same_group_double_erasure":("INCOMPLETE",False,[],False),
"parity_erasure_sources_complete":("DECODED",True,[],True),
"mixed_generation":("REJECT_INVALID_PROVENANCE",False,[],False),
"criticality_metadata_mismatch":("REJECT_INVALID_PROVENANCE",False,[],False),}
