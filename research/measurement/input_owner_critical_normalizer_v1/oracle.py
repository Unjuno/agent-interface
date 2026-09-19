from copy import deepcopy
MAP={'focus_changed':'FOCUS_CHANGED','expired':'LEASE_EXPIRED','surface_changed':'AUTHORITY_REVOKED','cancelled':'AUTHORITY_REVOKED','stop_requested':'AUTHORITY_REVOKED'}
def goodstr(x): return type(x) is str and bool(x.strip())
def oracle(e):
    if type(e) is not dict or set(e)!={'event_id','seq','received_ns','session','target','stream','raw'}: raise ValueError
    if not all(goodstr(e[k]) for k in ('event_id','session','target','stream')) or type(e['seq']) is not int or e['seq']<0 or type(e['received_ns']) is not int or e['received_ns']<0 or type(e['raw']) is not dict: raise ValueError
    q=e['raw']; ev=q.get('event')
    if ev=='owner_release':
        if set(q)!={'event','reason','verified','buttons_down','keys_down','verified_ns','valid_until_ns'} or not goodstr(q.get('reason')) or type(q.get('verified')) is not bool or type(q.get('buttons_down')) is not list or type(q.get('keys_down')) is not list or type(q.get('verified_ns')) is not int or q['verified_ns']<0 or (q.get('valid_until_ns') is not None and (type(q['valid_until_ns']) is not int or q['valid_until_ns']<0)): raise ValueError
        if not q['verified'] or q['buttons_down'] or q['keys_down']: kind='SAFETY_VIOLATION'
        elif q['reason'] in MAP: kind=MAP[q['reason']]
        else: raise ValueError
    elif ev in ('owner_failed','cleanup_failed'):
        if set(q)!={'event','error','verified'} or not goodstr(q.get('error')) or q.get('verified') is not False: raise ValueError
        kind='SAFETY_VIOLATION'
    else: raise ValueError
    return {'kind':kind,'raw':deepcopy(q)}
