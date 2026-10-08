def classify_complete(events, expected_count):
    if type(expected_count) is not int or expected_count < 0 or not isinstance(events,list) or len(events)!=expected_count: return 'UNKNOWN'
    return classify(events)

def classify(events):
    if not isinstance(events, list): return 'UNKNOWN'
    for e in events:
        if not isinstance(e, dict) or set(e) != {'seq','kind','value','source'}: return 'UNKNOWN'
        if type(e['seq']) is not int or type(e['value']) is not int or e['source'] != 'object-A': return 'UNKNOWN'
    ordered = sorted(events, key=lambda e:e['seq'])
    if [e['seq'] for e in ordered] != list(range(len(ordered))): return 'UNKNOWN'
    state = 'NOT_RUN'
    for e in ordered:
        k = e['kind']
        if k == 'PREDICT': continue
        if k == 'ACTION' and state == 'NOT_RUN': state = 'PENDING'
        elif k == 'INTERMEDIATE' and state == 'PENDING': continue
        elif k == 'EFFECT' and state == 'PENDING': state = 'SUCCESS' if e['value'] == 0 else 'FAILED'
        elif k == 'FAIL' and state == 'PENDING': state = 'FAILED'
        elif k == 'REVERT' and state == 'SUCCESS': state = 'SUCCESS_THEN_REVERT'
        else: return 'UNKNOWN'
    return state
