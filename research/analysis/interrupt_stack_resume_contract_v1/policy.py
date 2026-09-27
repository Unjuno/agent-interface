POLICIES = ('POP_ONLY','QUEUE_VERSION_ONLY','EVIDENCE_BOUND_RESUME')
DECISIONS = ('CANCELED','WAIT_INTERRUPT','RECONCILE_RESULT','YIELD_STALE','REPLAN_QUEUE','REVALIDATE_TARGET','RESUME')

def evidence_bound(state):
    if state['task_active'] is False:
        d='CANCELED'
    elif state['interrupt_resolved'] is False:
        d='WAIT_INTERRUPT'
    elif state['pending_result']=='UNKNOWN':
        d='RECONCILE_RESULT'
    elif state['source_fresh'] is False:
        d='YIELD_STALE'
    elif state['queue_version_same'] is False:
        d='REPLAN_QUEUE'
    elif state['target_identity_same'] is False:
        d='REVALIDATE_TARGET'
    else:
        d='RESUME'
    return {'decision':d,'resume_eligible':d=='RESUME','input_authority':False}

def pop_only(state):
    if state['task_active'] is False:
        d='CANCELED'
    elif state['interrupt_resolved'] is False:
        d='WAIT_INTERRUPT'
    else:
        d='RESUME'
    return {'decision':d,'resume_eligible':d=='RESUME','input_authority':False}

def queue_only(state):
    if state['task_active'] is False:
        d='CANCELED'
    elif state['interrupt_resolved'] is False:
        d='WAIT_INTERRUPT'
    elif state['queue_version_same'] is False:
        d='REPLAN_QUEUE'
    else:
        d='RESUME'
    return {'decision':d,'resume_eligible':d=='RESUME','input_authority':False}

def evaluate(policy,state):
    return {'POP_ONLY':pop_only,'QUEUE_VERSION_ONLY':queue_only,'EVIDENCE_BOUND_RESUME':evidence_bound}[policy](state)
