def oracle(initial,events):
    status='PENDING'; verified=False
    oid,itok,key,gen,attempt=initial
    for e in events:
        if status in ('RELEASE_CONFIRMED','RELEASE_UNCONFIRMED_BACKEND_LOST'):
            continue
        if not isinstance(e,dict) or not isinstance(e.get('kind'),str):
            return ('ERROR',False)
        if e['kind']=='backend_lost':
            status='RELEASE_UNCONFIRMED_BACKEND_LOST'; verified=False; continue
        if e['kind']!='release_observation': return ('ERROR',False)
        keys=('owner_id','intent_token','key','server_generation','cleanup_attempt_id','key_up')
        if any(k not in e for k in keys) or not isinstance(e['key_up'],bool): return ('ERROR',False)
        same=(e['owner_id'],e['intent_token'],e['key'],e['server_generation'],e['cleanup_attempt_id'])==(oid,itok,key,gen,attempt)
        if same and e['key_up']:
            status='RELEASE_CONFIRMED'; verified=True
    return status,verified
