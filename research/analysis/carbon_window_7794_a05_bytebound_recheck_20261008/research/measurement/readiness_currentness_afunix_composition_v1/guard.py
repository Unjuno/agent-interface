import time
from protocol import decode_record,SCOPE,GENERATION,MAX_AGE_NS,REG_VALID,REG_HARD,REG_AMBIG,READY

def _common(data,last_seq,now_ns,expected_scope,expected_generation):
    row=decode_record(data)
    if row['scope']!=expected_scope: raise ValueError('scope')
    if row['generation']!=expected_generation: raise ValueError('generation')
    if type(row['seq']) is not int or row['seq']<=last_seq: raise ValueError('nonadvancing_seq')
    if now_ns is None: now_ns=time.perf_counter_ns()
    age=now_ns-row['published_ns']
    if age<0 or age>MAX_AGE_NS: raise ValueError('stale_time')
    return row

def currentness_only(data,last_seq,now_ns=None,expected_scope=SCOPE,expected_generation=GENERATION):
    row=_common(data,last_seq,now_ns,expected_scope,expected_generation)
    if row['regime']==REG_VALID: disposition='ADMIT'
    elif row['regime']==REG_HARD: disposition='REFUSE_HARD'
    elif row['regime']==REG_AMBIG: disposition='YIELD_AMBIGUOUS'
    else: raise ValueError('regime')
    return disposition,row['seq']

def composite_guard(data,last_seq,expected_readiness_generation,now_ns=None,expected_scope=SCOPE,expected_generation=GENERATION):
    row=_common(data,last_seq,now_ns,expected_scope,expected_generation)
    if row['regime']==REG_HARD: disposition='REFUSE_HARD'
    elif row['regime']==REG_AMBIG: disposition='YIELD_AMBIGUOUS'
    elif row['readiness_generation']!=expected_readiness_generation: disposition='REFUSE_STALE_READINESS'
    elif row['readiness_state']!=READY: disposition='REFUSE_NONREADY'
    else: disposition='ADMIT'
    return disposition,row['seq']
