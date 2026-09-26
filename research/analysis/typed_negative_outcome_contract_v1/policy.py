LABELS=(
'SUCCEEDED','IN_PROGRESS','BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND',
'CAPABILITY_UNSUPPORTED','CONFLICT','IMPOSSIBLE_UNDER_CONSTRAINTS','FAILED_UNKNOWN')
TERMINAL={'SUCCEEDED','CAPABILITY_UNSUPPORTED','IMPOSSIBLE_UNDER_CONSTRAINTS'}

def classify(e):
    if e['freshness']!='CURRENT' or e['completeness']!='COMPLETE' or e.get('contradictory') is True:
        return {'label':'FAILED_UNKNOWN','retryable':False,'required_change':'refresh_evidence','authority_granted':False}
    f=e['family']
    if f=='SUCCEEDED': return {'label':f,'retryable':False,'required_change':'none','authority_granted':False}
    if f=='IN_PROGRESS': return {'label':f,'retryable':False,'required_change':'wait_for_completion','authority_granted':False}
    if f=='BLOCKED':
        ok=e['retry_context']=='IDENTICAL_RETRY_VALID'
        return {'label':f,'retryable':ok,'required_change':'none' if ok else 'wait_for_blocker_change','authority_granted':False}
    if f=='AUTHORITY_REQUIRED': ch='obtain_authority'
    elif f=='TARGET_NOT_FOUND': ch='change_target_or_observe'
    elif f=='CAPABILITY_UNSUPPORTED': ch='change_capability_or_route'
    elif f=='CONFLICT': ch='resolve_conflict'
    elif f=='IMPOSSIBLE_UNDER_CONSTRAINTS': ch='relax_constraints'
    elif f=='FAILED_UNKNOWN': ch='gather_more_evidence'
    else: raise ValueError('unknown family')
    return {'label':f,'retryable':False,'required_change':ch,'authority_granted':False}

def coarse(e):
    if e['status']=='ok':
        return {'label':'SUCCEEDED','retryable':False,'required_change':'none','authority_granted':False}
    if e['status']=='working':
        return {'label':'IN_PROGRESS','retryable':False,'required_change':'wait_for_completion','authority_granted':False}
    if e['timeout']:
        return {'label':'BLOCKED','retryable':True,'required_change':'none','authority_granted':False}
    return {'label':'IMPOSSIBLE_UNDER_CONSTRAINTS','retryable':False,'required_change':'change_goal','authority_granted':False}
