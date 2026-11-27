from audit_live_reconciliation import reconcile_cancellation_custody as original, verified_empty

def reconcile_cancellation_custody(events, guard_id):
    """Add conservative admission checks; this is not an event-order auditor."""
    if not isinstance(events,list) or not isinstance(guard_id,str) or not guard_id:
        raise ValueError('invalid events or guard identity')
    kinds={'cancel_requested','terminal','input_admission','input_released'}
    for event in events:
        if not isinstance(event,dict): raise ValueError('event must be an object')
        if event.get('event') in kinds and (not isinstance(event.get('id'),str) or not event['id']):
            raise ValueError('event identity must be a nonempty string')
    result=original(events,guard_id)
    invalid=set(result['unaccounted_cancel_ids'])
    cancels=[e for e in events if e.get('event')=='cancel_requested' and e.get('matched') is True]
    ids=[e['id'] for e in cancels]
    for ident in set(ids):
        terminals=[e for e in events if e.get('event')=='terminal' and e.get('id')==ident]
        releases=[e for e in events if e.get('event')=='input_released' and e.get('id')==ident]
        admissions=[e for e in events if e.get('event')=='input_admission' and e.get('id')==ident]
        if ids.count(ident)!=1 or len(terminals)!=1 or len(releases)>1:
            invalid.add(ident);continue
        if not admissions:continue
        tokens=[e.get('intent_token') for e in admissions]
        if any(not isinstance(t,str) or not t for t in tokens) or len(set(tokens))!=1:
            invalid.add(ident);continue
        token=tokens[0]; interruption=terminals[0].get('interruption')
        if not isinstance(interruption,dict):invalid.add(ident);continue
        record=interruption.get('record'); release=releases[0] if len(releases)==1 else None
        owner=release.get('owner_release') if release else None
        if not (interruption.get('intent_token')==token and verified_empty(record) and record.get('intent_token')==token and release and release.get('intent_token')==token and verified_empty(owner) and owner.get('intent_token')==token and owner.get('reason')=='cancelled'):
            invalid.add(ident)
    result['unaccounted_cancel_ids']=sorted(invalid)
    result['cancel_terminal_releases_empty']=not invalid
    return result
