from __future__ import annotations
from copy import deepcopy
from queue_contract import Record
ENVELOPE={'event_id','seq','received_ns','session','target','stream','raw'}
RELEASE_KIND={'focus_changed':'FOCUS_CHANGED','expired':'LEASE_EXPIRED','surface_changed':'AUTHORITY_REVOKED','cancelled':'AUTHORITY_REVOKED','stop_requested':'AUTHORITY_REVOKED'}

def _nonblank(x): return type(x) is str and bool(x.strip())
def _envelope(e):
    if type(e) is not dict or set(e)!=ENVELOPE: raise ValueError('envelope')
    if not all(_nonblank(e[k]) for k in ('event_id','session','target','stream')): raise ValueError('identity')
    if type(e['seq']) is not int or e['seq']<0 or type(e['received_ns']) is not int or e['received_ns']<0: raise ValueError('time_or_seq')
    if type(e['raw']) is not dict: raise ValueError('raw')

def normalize_one(e):
    _envelope(e); raw=e['raw']; event=raw.get('event')
    kind=None; disposition=None
    if event=='owner_release':
        required={'event','reason','verified','buttons_down','keys_down','verified_ns','valid_until_ns'}
        if set(raw)!=required: raise ValueError('release_shape')
        if not _nonblank(raw['reason']) or type(raw['verified']) is not bool or type(raw['buttons_down']) is not list or type(raw['keys_down']) is not list: raise ValueError('release_fields')
        if type(raw['verified_ns']) is not int or raw['verified_ns']<0: raise ValueError('release_time')
        if raw['valid_until_ns'] is not None and (type(raw['valid_until_ns']) is not int or raw['valid_until_ns']<0): raise ValueError('valid_until')
        neutral=not raw['buttons_down'] and not raw['keys_down']
        if not raw['verified'] or not neutral:
            kind='SAFETY_VIOLATION'; disposition='release_unverified'
        else:
            if raw['reason'] not in RELEASE_KIND: raise ValueError('release_reason_out_of_scope')
            kind=RELEASE_KIND[raw['reason']]; disposition='verified_release'
    elif event in ('owner_failed','cleanup_failed'):
        if set(raw)!={'event','error','verified'} or not _nonblank(raw.get('error')) or raw.get('verified') is not False: raise ValueError('failure_shape')
        kind='SAFETY_VIOLATION'; disposition='owner_failure'
    else:
        raise ValueError('event_out_of_scope')
    record=Record(e['event_id'],e['seq'],e['received_ns'],e['session'],e['target'],e['stream'],kind)
    return {'record':record,'raw':deepcopy(raw),'normalization':{'kind':kind,'disposition':disposition},'grants_input_authority':False}

def normalize_stream(rows):
    out=[]; seen=set(); prev=None
    for e in rows:
        n=normalize_one(e); r=n['record']
        if r.event_id in seen: raise ValueError('duplicate_event_id')
        if prev is not None and r.seq<=prev: raise ValueError('nonmonotonic_seq')
        seen.add(r.event_id); prev=r.seq; out.append(n)
    return out
