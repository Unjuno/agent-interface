"""Independent literal expected outcomes; no candidate imports."""
EXPECTED={
"pure_direct":("ADMIT",True,False),
"direct_read":("ADMIT",True,False),
"polymorphic_network_instantiation":("REJECT_UNDECLARED",False,False),
"wrapper_masks_nested_write":("REJECT_UNDECLARED",False,False),
"branch_union_false_reject":("REJECT_UNDECLARED",False,True),
"native_unknown":("EFFECT_UNKNOWN",False,False),
"remote_unknown":("EFFECT_UNKNOWN",False,False),
"valid_transitive_read_observe":("ADMIT",True,False),
"contained_effect_row":("ADMIT",True,False),
}
