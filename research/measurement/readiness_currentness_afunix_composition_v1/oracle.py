from protocol import REG_VALID,REG_HARD,REG_AMBIG,READY

def decide(regime,record_ready_gen,record_ready_state,expected_ready_gen):
    if regime==REG_HARD:return 'REFUSE_HARD'
    if regime==REG_AMBIG:return 'YIELD_AMBIGUOUS'
    if regime!=REG_VALID:raise ValueError('regime')
    if record_ready_gen!=expected_ready_gen:return 'REFUSE_STALE_READINESS'
    if record_ready_state!=READY:return 'REFUSE_NONREADY'
    return 'ADMIT'
