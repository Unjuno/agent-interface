"""Independent review oracle; not imported by candidate or model runner."""
def expected(wanted,target,decoy):
    decision='REFUSE';prefix=''
    if not decoy and target==wanted:decision='NO_REPAIR'
    elif not decoy and target and target==wanted[1:]:decision='INSERT_PREFIX';prefix=wanted[0]
    return dict(decision=decision,observed_target=target,observed_decoy=decoy,prefix=prefix)
